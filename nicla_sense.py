import threading
from zoneinfo import ZoneInfo
from bleak import BleakClient, BleakScanner, BleakError
import struct
import asyncio
from logger import Logger
from datetime import datetime
import sys

class BLEClient:
    def __init__(self,
                 polling_interval = 10,
                 dev_name = "NiclaSenseME-B806",
                 timestamp_format = "%Y%m%d%H%M%S",
                 timezone = ZoneInfo("Asia/Singapore"),
                 delay_tolerance = 600,
                 log_level = "INFO",
                 stop_event = None):
        '''
            Wrapper class for BLE communication with NiclaSenseME
            polling_interval: Interval between each polling in seconds
            dev_name: Name of the BLE device
            timestamp_format: Format of the timestamp
            timezone: Timezone for formatting timestamp
            delay_tolerance: Tolerance for time since last readings of other sensors (seconds), 
                if delay exceeds this value, previous sensor readings by other sensors will be discarded
            log_level: Logging level
            stop_event: Synchronization signal for stopping the BLEClient
        '''
        self.polling_interval = polling_interval
        self.timestamp_format = timestamp_format
        self.timezone = timezone
        self.device_name = dev_name
        self.sensor_map = {
            "temp" : (BLEClient.formatUUID("2001"), "<f"),
            "pressure" : (BLEClient.formatUUID("4001"), "<f"),
            "humidity" : (BLEClient.formatUUID("3001"), "<I"),
            "gas" : (BLEClient.formatUUID("9003"), "<I"),
            "co2" : (BLEClient.formatUUID("9002"), "<i"),
        }
        self.sensorMapNotif = {
            "accel" : (BLEClient.formatUUID("5001"), "<fff"),
            "gyro" : (BLEClient.formatUUID("6001"), "<fff"),
            "quat" : (BLEClient.formatUUID("7001"), "<ffff"),
        }
        self.buffer = {
            "timestamp" : 20250101000000,
            "temp" : 0,
            "humidity" : 0,
            "pressure" : 0,
            "gas" : 0,
            "co2" : 0,
            "accel" : (0, 0, 0),
            "gyro" : (0, 0, 0),
            "quat" : (0, 0, 0, 0),
        }
        self.device = None
        self.logger = Logger("BLEClient", log_level).get()
        self.stop_event = stop_event
        self.delay_tolerance = delay_tolerance
        self.lock = threading.Lock()

    @staticmethod
    def formatUUID(id):
        return f"19b10000-{id}-537e-4f6c-d104768a1214"
    
    async def main(self):
        await self.find_nicla_device()  # Ensure the device is found
        if self.device:  # Proceed only if a device is found
            await self.listen_to_device(self.device)  # Start listening to the device

    def run(self):
        asyncio.run(self.main())
    
    def retreive(self, buffer):
        self.lock.acquire()
        
        main_buffer_time = datetime.strptime(str(buffer["timestamp"]), self.timestamp_format)
        curr_buffer_time = datetime.strptime(str(self.buffer["timestamp"]), self.timestamp_format)
        dt = (curr_buffer_time - main_buffer_time).seconds
        dt *= 1 if curr_buffer_time > main_buffer_time else -1
        self.logger.debug(f"Time between main buffer and current buffer: {dt}s")

        if dt >= 0:
            if dt > self.delay_tolerance:
                self.logger.warning(f"Data in main buffer outdated by >{self.delay_tolerance}s!")
                for key in buffer:
                    if key != "timestamp":
                        buffer[key] = None
            for key in self.buffer:
                if key not in buffer:
                    self.logger.error(f"Key {key} not found in main data buffer!")
                buffer[key] = self.buffer[key]

        self.lock.release()
            
    async def find_nicla_device(self):
        self.device = await BleakScanner.find_device_by_name(self.device_name)
        if self.device is None:
            self.logger.fatal(f"Device {self.device_name} not found!")
            return None
        else:
            self.logger.info(f"Device {self.device_name} found!")
            return self.device

    def notif_handler(self, sender, data, sensor_name, data_format):
        """Handle incoming notifications."""
        self.buffer[sensor_name] = struct.unpack(data_format, data)

    async def listen_to_device(self, device):
        """Connect to the BLE device and listen for data."""
        try:
            while not self.stop_event.is_set():
                try:
                    self.logger.debug("Connecting to device...")
                    self.device = await BleakScanner.find_device_by_name(self.device_name)
                    async with BleakClient(self.device) as client:
                        self.logger.info(f"Connected to {self.device_name}")                        
                        while not self.stop_event.is_set():

                            # Timestamp of data is taken at the start of polling
                            start_time = datetime.now(self.timezone)
                            self.lock.acquire()

                            for sensor, (uuid, fmt) in self.sensor_map.items():
                                data = await client.read_gatt_char(uuid)
                                value = struct.unpack(fmt, data)[0]
                                self.buffer[sensor] = value

                            for sensor, (uuid, fmt) in self.sensorMapNotif.items():
                                await client.start_notify(
                                    uuid, 
                                    lambda x, y : self.notif_handler(x, 
                                                                     y, 
                                                                     sensor_name=sensor, 
                                                                     data_format=fmt))
                                await client.stop_notify(uuid)

                            # Timestamp is updated at the end of polling to ensure all
                            # values has already been updated
                            self.buffer["timestamp"] = start_time.strftime(self.timestamp_format)
                            self.lock.release()

                            self.logger.info("Received update from NiclaSenseME")
                            for sensor, value in self.buffer.items():
                                self.logger.debug(f"{sensor}: {value}")
                            self.logger.debug("--------------------------------")
                            
                            for _ in range(self.polling_interval * 2):
                                if self.stop_event.is_set():
                                    break
                                await asyncio.sleep(0.5)  # Adjust polling interval

                except BleakError as e:
                    self.logger.error(f"Error during BLE communication: {e}")
                except TimeoutError as e:
                    self.logger.warning(f"BLE Connection Timeout error")

        except asyncio.CancelledError:
            self.logger.info("Listening task canceled, cleaning up...")           
        finally:
            self.logger.debug("BLEClient stopped!")
