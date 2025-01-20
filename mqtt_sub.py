import threading
from zoneinfo import ZoneInfo
import paho.mqtt.client as mqtt
import ssl
import base64
from PIL import Image
import io
from datetime import datetime
import os
import csv
import numpy as np
from logger import Logger
import time

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

class MQTTSubscriber:
    def __init__(self, 
                 mqtt_broker_ip = '192.168.0.117', 
                 mqtt_port = 1883, 
                 ca_cert_path = '/home/ph/hardware/ca.crt', 
                 client_cert_path = '/home/ph/hardware/client.crt', 
                 client_key_path = '/home/ph/hardware/client.key', 
                 sensor_topic = 'sensor/#', 
                 username = 'cloud', 
                 password = '3', 
                 image_dir = os.path.join(DIR_PATH, 'data', 'images'),
                 timestamp_format = "%Y%m%d%H%M%S",
                 timezone = ZoneInfo("Asia/Singapore"),
                 delay_tolerance = 600,
                 log_level = "INFO",
                 stop_event = None):
        self.timestamp_format = timestamp_format
        self.timezone = timezone
        self.mqtt_broker_ip = mqtt_broker_ip
        self.mqtt_port = mqtt_port
        self.ca_cert_path = ca_cert_path
        self.client_cert_path = client_cert_path
        self.client_key_path = client_key_path
        self.sensor_topic = sensor_topic
        self.username = username
        self.password = password
        self.image_dir = image_dir
        self.buffer = {
            "timestamp": 20250101000000,
            "image": None,
            "aec_level": None,
            "agc_gain": None,
            "amb": None,
            "r": None,
            "g": None,
            "b": None
        }
        self.logger = Logger("MQTTSubscriber", log_level).get()
        self.stop_event = stop_event
        self.delay_tolerance = delay_tolerance
        self.lock = threading.Lock()


    def run(self):
        if not os.path.isdir(self.image_dir):
            self.logger.critical(f"Image is to be saved at {self.image_dir} but it is not present.")
            self.logger.critical("Check that the USB is properly mounted and the target directory is correct")
            raise Exception("Image directory not found!")
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.mqtt_broker_ip, self.mqtt_port, 60)
        self.client.loop_start()
        while not self.stop_event.is_set():
            time.sleep(1)
            pass
        self.client.disconnect()
        self.client.loop_stop()
        self.logger.info("MQTT Subscriber stopped!")

    def on_connect(self, client, userdata, flags, rc):
        self.logger.info(f"Connected with result code {rc}")
        client.subscribe(self.sensor_topic)

    def on_message(self, client, userdata, msg):
        payload = msg.payload
        msg_type = payload[:3]
        if msg_type == b'IMG':
            self.decode_image_str(payload[3:])
        elif msg_type == b'SNR':
            self.update_sensor_data(payload[3:].decode())
        else:
            self.logger.error(f"Unknown message type {msg_type} received! Check message definition!")

    def decode_image_str(self, image_string):
        timestamp = image_string[0:14].decode()
        if all(c == '0' for c in timestamp):
            # Time not set on ESP32CAM, use time of receival instead
            timestamp = datetime.now(self.timezone).strftime(self.timestamp_format)
        cam_id = image_string[14:16].decode()

        self.lock.acquire()
        self.buffer["image"] = cam_id + "_" + timestamp + ".jpg"
        self.buffer["aec_level"] = image_string[16:21].decode()
        self.buffer["agc_gain"] = image_string[21:24].decode()
        image_string = image_string[24:]
        self.buffer["timestamp"] = timestamp
        self.lock.release()

        self.logger.debug(f"Decoding image - Camera {cam_id}: {timestamp} |" + \
                          f" aec: {self.buffer['aec_level']} |" + \
                          f" agc_gain: {self.buffer['agc_gain']}")

        # Decode the image and save to file
        image_data = base64.b64decode(image_string)
        image_bytes = bytes(image_data)
        image_stream = io.BytesIO(image_bytes)
        image = Image.open(image_stream)
        image.save(os.path.join(self.image_dir, self.buffer["image"]))  

    def update_sensor_data(self, msg):
        self.logger.info(f"Updating sensor data: {msg}")

        self.lock.acquire()
        for data in msg.split(','):
            name, val = data.split(':')
            self.buffer[name] = int(val)
        self.lock.release()


    def retreive(self, buffer):
        self.lock.acquire()
        
        main_buffer_time = datetime.strptime(str(buffer["timestamp"]), self.timestamp_format)
        curr_buffer_time = datetime.strptime(str(self.buffer["timestamp"]), self.timestamp_format)
        dt = (curr_buffer_time - main_buffer_time).seconds
        dt *= 1 if curr_buffer_time > main_buffer_time else -1
        self.logger.debug(f"Time between main buffer and current buffer: {dt}s")
        if dt > self.delay_tolerance:
            self.logger.warning(f"Data in main buffer outdated by >{self.delay_tolerance}s!")
            for key in buffer:
                if key != "timestamp":
                    buffer[key] = None

        if dt >= 0:
            for key in self.buffer:
                if key not in buffer:
                    self.logger.error(f"Key {key} not found in main data buffer!")
                buffer[key] = self.buffer[key]
        
        self.lock.release()

