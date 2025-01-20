import csv
from logger import Logger
from os.path import join, dirname, abspath

DIR_PATH = dirname(abspath(__file__))

class DataEntry:
    def __init__(self, 
                 timestamp_format = "%Y%m%d%H%M%S",
                 data_file = join(DIR_PATH, 'data', 'data.csv'),
                 log_level = "INFO",
                 ):
        self.data = {
            "timestamp": 20250101000000,
            "image": None,
            "aec_level": None,
            "agc_gain": None,
            "amb": None,
            "r": None,
            "g": None,
            "b": None,
            "temp": None,
            "pressure": None,
            "humidity": None,
            "gas": None,
            "co2": None,
            "accel": (0, 0, 0),
            "gyro": (0, 0, 0),
            "quat": (0, 0, 0, 0),
        }
        self.data_file = data_file
        self.timestamp_format = timestamp_format
        self.logger = Logger("DataEntry", log_level).get()

    def __str__(self):
        res = ""
        for key in self.data:
            res += f"{key}: {self.data[key]}, "
        res = res[:-2]
        return res

    def to_csv_row(self):
        """Convert the object into a list suitable for writing to a CSV file."""
        res = []
        for key in self.data:
            res.append(self.data[key])
        return res

    def write_to_csv(self):
        with open(self.data_file, mode="a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(self.to_csv_row())

    def print_header(self):
        res = ""
        for key in self.data:
            res += f"{key},"
        res = res[:-2]
        self.logger.debug(res)
        return res