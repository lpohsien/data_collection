from datetime import datetime
from apds9960_reader import APDS9960Reader
from mqtt_sub import MQTTSubscriber
from nicla_sense import BLEClient
from dataset import DataEntry
from picam import PiCam
import threading
import signal
from logger import Logger
import time
from tzlocal import get_localzone
from os.path import dirname, abspath, join

DATA_DIR_PATH = join(dirname(abspath(__file__)), 'data')

stop_event = threading.Event()
logger = Logger("Main", "DEBUG").get()

def signal_handler(sig, frame):
    print("\nCtrl-C detected! Stopping threads...")
    stop_event.set()  # Signal threads to stop

def fast_sleep(seconds, resolution=2):
    for _ in range(int(seconds / resolution)):
        if stop_event.is_set():
            break
        time.sleep(resolution)

def time_dependent_settings(timezone):
    image_interval = 30 * 60 # 30 minutes
    ev_bracket = (-2, 2, 5)
    
    # Get current time
    current_time = datetime.now(timezone)
    current_hour = current_time.hour

    if current_hour >= 23 or current_hour < 4:
        image_interval = 60 * 60
        ev_bracket = (0, 0, 1)

    if (current_hour >= 5 and current_hour < 7) or (current_hour >= 17 and current_hour < 19):
        image_interval = 10 * 60

    return image_interval, ev_bracket      

   

def main():
    # timezone = ZoneInfo("Asia/Singapore")
    timezone = get_localzone()
    logger.info("Starting data collection server at " + str(datetime.now(timezone)))
    data_entry = DataEntry(log_level="DEBUG", data_file=join(DATA_DIR_PATH, 'data.csv'))
    mqtt_sub = MQTTSubscriber(log_level="INFO", stop_event=stop_event, timezone=timezone, image_dir=join(DATA_DIR_PATH, 'images'))
    nicla_sense = BLEClient(log_level="INFO", stop_event=stop_event, timezone=timezone)
    camera = PiCam(log_level="INFO", timezone=timezone, image_dir=join(DATA_DIR_PATH, 'images'))
    apds9960 = APDS9960Reader()
    mqtt_thread = threading.Thread(target=mqtt_sub.run, daemon=True)
    nicla_thread = threading.Thread(target=nicla_sense.run, daemon=True)
    mqtt_thread.start()
    nicla_thread.start()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while not stop_event.is_set():

            # Time-dependent settings
            image_interval, ev_bracket = time_dependent_settings(timezone)   
            logger.info(f"Using settings: {image_interval} seconds, {ev_bracket} EV bracketing")

            fast_sleep(image_interval)
        
            # Get most recent sensor data, tolerate delay up to 600 seconds
            mqtt_sub.retreive(data_entry.data)
            nicla_sense.retreive(data_entry.data)
            logger.debug(str(data_entry))

            # Retrieve APDS9960 data, assumed to have negligible delay
            apds9960.retrieve(data_entry.data)
            # Capture image
            metadatas = camera.ev_bracketing_capture(*ev_bracket)
            for metadata in metadatas:
                
                image_timestamp = datetime.strptime(metadata["captureTimestamp"], camera.timestamp_format)
                data_timestamp = datetime.strptime(str(data_entry.data["timestamp"]), data_entry.timestamp_format)
                if (image_timestamp - data_timestamp).seconds > 600:
                    logger.warning("Image timestamp is more than 10 minutes ahead of sensor data timestamp!")

                for key in metadata:
                    data_entry.data[key] = metadata[key]
                data_entry.write_to_csv()
            
            data_entry.print_header()


        mqtt_thread.join()
        nicla_thread.join()
    except KeyboardInterrupt:
        stop_event.set()
        mqtt_thread.join()
        nicla_thread.join()
        logger.debug("All threads terminated successfully!")
        logger.info(data_entry.print_header())


if __name__ == "__main__":
    main()
