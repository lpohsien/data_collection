import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfoNotFoundError
from tzlocal import get_localzone

class Logger:
    def __init__(self, name="Logger", log_level="INFO",):
        self.logger = logging.getLogger(name)  # Use the provided name instead of hardcoding "Logger"
        self.logger.setLevel(log_level)

        if not self.logger.handlers:  # Prevent duplicate handlers
            console_handler = logging.StreamHandler(sys.stdout)
            log_format = logging.Formatter(
                '%(asctime)s [%(name)s][%(levelname)s] - %(message)s'
            )
            log_format.datefmt = "%Y-%m-%d %H:%M:%S"
            logging.Formatter.converter = lambda *args: datetime.now(tz=get_localzone()).timetuple()
            console_handler.setFormatter(log_format)
            self.logger.addHandler(console_handler)

    def get(self):
        return self.logger
    
