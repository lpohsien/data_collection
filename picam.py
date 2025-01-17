import os
from picamera2 import Picamera2
import time
from logger import Logger
from datetime import datetime
from zoneinfo import ZoneInfo

class PiCam:
    def __init__(self, 
                 image_dir="/mnt/USBDRIVE/cp4101_data/images",
                 location_id = "00",
                 timestamp_format = "%Y%m%d%H%M%S",
                 timezone = ZoneInfo("Asia/Singapore"),
                 log_level="INFO"):
        self.picam2 = Picamera2()
        self.still_config = self.picam2.create_still_configuration(
                                main={"size": (1280, 1024)},  # Set resolution to SXGA
                                display=None  # Disable preview display
                            )
        self.picam2.configure(self.still_config)
        self.logger = Logger("PiCam", log_level).get()
        self.image_dir = image_dir
        self.timestamp_format = timestamp_format
        self.location_id = location_id
        self.timezone = timezone
        self.image_format = self.picam2.stream_configuration("main")
        self.picam2.start()
        time.sleep(1)

    def ev_bracketing_capture(self, min, max, num_frames):
        interval = None
        if num_frames == 1:
            interval = int((max - min) / 2)
        else:
            interval = int((max - min) / (num_frames - 1))
        metadatas = []
        for i in range(num_frames):
            
            ev = min + i * interval
            self.picam2.set_controls({"ExposureValue": ev}) 
            time.sleep(1)

            self.logger.debug(f"Capturing image with EV {ev}")
            metadata = self.capture()
            metadata["ev"] = ev

            metadatas.append(metadata)

        return metadatas

    def capture(self, **kwargs):
        timestamp = datetime.now(self.timezone).strftime(self.timestamp_format)
        filename = f"{self.location_id}_{timestamp}.jpg"
        full_filename = os.path.join(self.image_dir, filename)
        
        job = self.picam2.switch_mode_and_capture_file(self.still_config, full_filename, wait=False)
        metadata = self.picam2.wait(job)

        self.logger.info(f"Captured: {filename}")
        metadata["captureTimestamp"] = timestamp
        metadata["image_format"] = self.image_format
        metadata["image"] = filename
        self.logger.debug(metadata)
        self.logger.debug("--------------------------")
        return metadata

    def close(self):
        self.picam2.stop()

