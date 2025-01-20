# Adapted from https://github.com/liske/python-apds9960/blob/master/rpi/test_ambient.py

from apds9960.const import *
from apds9960 import APDS9960
# import RPi.GPIO as GPIO
from smbus2 import SMBus
from logger import Logger
from time import sleep


class APDS9960Reader:
    def __init__(self, port = 1, log_level = "INFO"):
        self.bus = SMBus(port)
        self.apds = APDS9960(self.bus)
        self.apds.enableLightSensor()
        self.logger = Logger("APDS9960Reader", log_level).get()
        self.logger.info("APDS9960Reader initialized")

    def retrieve(self, buffer):
        val = self.apds.readAmbientLight()
        r = self.apds.readRedLight()
        g = self.apds.readGreenLight()
        b = self.apds.readBlueLight()
        buffer['amb'] = val
        buffer['r'] = r
        buffer['g'] = g
        buffer['b'] = b
        self.logger.info("Ambient light data retrieved from APDS9960")
        return buffer