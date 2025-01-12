from datetime import datetime
from mqtt_sub import MQTTSubscriber
from nicla_sense import BLEClient
from dataset import DataEntry
from picam import PiCam
import threading
import signal
from logger import Logger
import time
from zoneinfo import ZoneInfo

stop_event = threading.Event()
logger = Logger("Main", "DEBUG").get()

def signal_handler(sig, frame):
    print("\nCtrl-C detected! Stopping threads...")
    stop_event.set()  # Signal threads to stop

def fast_sleep(seconds, resolution=0.5):
    for _ in range(int(seconds / resolution)):
        if stop_event.is_set():
            break
        time.sleep(resolution)

def main():
    timezone = ZoneInfo("Asia/Singapore")
    data_entry = DataEntry(log_level="DEBUG")
    mqtt_sub = MQTTSubscriber(log_level="INFO", stop_event=stop_event, timezone=timezone)
    nicla_sense = BLEClient(log_level="INFO", stop_event=stop_event, timezone=timezone)
    camera = PiCam(log_level="INFO", timezone=timezone)
    mqtt_thread = threading.Thread(target=mqtt_sub.run, daemon=True)
    nicla_thread = threading.Thread(target=nicla_sense.run, daemon=True)
    mqtt_thread.start()
    nicla_thread.start()

    signal.signal(signal.SIGINT, signal_handler)

    try:
        while not stop_event.is_set():
            fast_sleep(60 * 30)
        
            # Get most recent sensor data
            mqtt_sub.retreive(data_entry.data)
            nicla_sense.retreive(data_entry.data)
            logger.debug(str(data_entry))

            # Capture image
            metadatas = camera.ev_bracketing_capture(-2, 2, 5)
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
