# Corrosion Sensors
# 2021-08-17 v02

import time
import board
from analogio import AnalogIn

# Temperature Converter Helpers
from cedargrove_unit_converter.temperature import (
    celsius_to_fahrenheit,
    heat_index,
    dew_point,
)


class CorrosionTemp:
    """A sensor class for the PyPortal's integral temperature sensor."""

    def __init__(self, sensor="ADT7410", temp_delay=0.5):
        import adafruit_adt7410  # Integral I2C temperature sensor

        self._corrosion_sensor = adafruit_adt7410.ADT7410(board.I2C())
        self._corrosion_sensor.reset = True  # Set the sensor to a known state
        self._corrosion_sensor.high_resolution = True

        self._temp_delay = temp_delay
        self._temp_c = None
        self._temp_f = None

    @property
    def temperature(self):
        return self._temp_c, self._temp_f

    def read(self):
        """Update the temperature current value"""
        time.sleep(self._temp_delay)  # Wait to read temperature value
        self._temp_c = round(self._corrosion_sensor.temperature, 1)  # Celsius
        self._temp_f = round(celsius_to_fahrenheit(self._temp_c), 1)  # Fahrenheit
        return


class CorrosionLight:
    """A sensor class for the PyPortal's integral light sensor."""

    def __init__(self):
        self._light_sensor = AnalogIn(board.LIGHT)
        self._light_avg = []
        for i in range(0, 25):
            self._light_avg.append(self._light_sensor.value)

    @property
    def raw(self):
        # Acquire the current and averaged raw light sensor value
        raw_avg, norm_avg, lux_avg = self.average()
        return self._light_avg[0], raw_avg

    @property
    def normalized(self):
        # Acquire the current and averaged normalized light sensor value
        raw_avg, norm_avg, lux_avg = self.average()
        norm = round(self._light_avg[0] / 65535, 3)
        return norm, norm_avg

    @property
    def lux(self):
        # Acquire the current and averaged lux light sensor value
        raw_avg, norm_avg, lux_avg = self.average()
        norm = round(self._light_avg[0] / 65535, 3)
        lux = round(norm * 1100, 1)  # 3.3v = 1100Lux (approximately)
        return lux, lux_avg

    def average(self):
        self._light_avg.pop()
        self._light_avg.insert(0, self._light_sensor.value)
        raw_avg = 0
        for i in range(0, 25):
            raw_avg = raw_avg + self._light_avg[i]
        raw_avg = raw_avg / 25
        norm_avg = round(raw_avg / 65535, 3)
        lux_avg = round(norm_avg * 1100, 1)  # 3.3v ~ 1100 Lux
        return raw_avg, norm_avg, lux_avg


class CorrosionTempHumid:
    """A sensor class for the SHT31D-based indoor/outdoor and the AM2320-based
    indoor temperature and humidity sensors."""

    def __init__(self, sensor="SHT31D", temp_delay=3, humid_delay=4, debug=False):
        if sensor == "SHT31D":
            import adafruit_sht31d  # I2C temperature/humidity sensor; indoor/outdoor

            self._corrosion_sensor = adafruit_sht31d.SHT31D(board.I2C())
        if sensor == "AM2320":
            import adafruit_am2320  # I2C temperature/humidity sensor; indoor

            self._corrosion_sensor = adafruit_am2320.AM2320(board.I2C())

        self._corrosion_sensor.heater = False  # turn heater OFF
        self._heater_on = False
        self._temp_delay = temp_delay  # Temperature measurement delay (sec)
        self._humid_delay = humid_delay  # Humidity measurement delay (sec)
        self._temp_c = None
        self._temp_f = None
        self._dew_c = None
        self._dew_f = None
        self._humid_pct = None
        self._corrosion_index = 0  # 0:Normal, 1:Warning, 2:ALERT

        self._debug = debug
        if self._debug:
            print("*Init:\n", self.__class__)
            print("*Init:\n", self.__dict__)

    @property
    def temperature(self):
        return self._temp_c, self._temp_f

    @property
    def dew_point(self):
        return self._dew_c, self._dew_f

    @property
    def humidity(self):
        return self._humid_pct

    @property
    def corrosion_index(self):
        return self._corrosion_index

    @property
    def heater_on(self):
        return self._heater_on

    @heater_on.setter
    def heater_on(self, heater=False):
        self._heater_on = heater
        if self._heater_on:
            self._corrosion_sensor.heater = True  # Turn sensor heater ON
        else:
            self._corrosion_sensor.heater = False  # Turn sensor heater OFF
        return

    def read(self):
        """Update the temperature and humidity with current values,
        calculate dew point and corrosion index"""
        time.sleep(self._temp_delay)  # Wait to read temperature value
        self._temp_c = self._corrosion_sensor.temperature
        if self._temp_c != None:
            self._temp_c = min(max(self._temp_c, -40), 125)  # constrain value
            self._temp_c = round(self._temp_c, 1)  # Celsius
            self._temp_f = round(celsius_to_fahrenheit(self._temp_c), 1)  # Fahrenheit
        else:
            self._temp_f = None
        time.sleep(self._humid_delay)  # Wait to read humidity value
        self._humid_pct = self._corrosion_sensor.relative_humidity
        if self._humid_pct != None:
            self._humid_pct = min(max(self._humid_pct, 0), 100)  # constrain value
            self._humid_pct = round(self._corrosion_sensor.relative_humidity, 1)

        # Calculate dew point values
        if None in (self._temp_c, self._humid_pct):
            self._dew_c = None
            self._dew_f = None
        else:
            self._dew_c = dew_point(self._temp_c, self._humid_pct)
            self._dew_f = round(celsius_to_fahrenheit(self._dew_c), 1)

        # calculate corrosion index value; keep former value if temp or dewpoint = None
        if None in (self._temp_c, self._dew_c):
            return
        else:
            if (self._temp_c <= self._dew_c + 2) or self._humid_pct >= 80:
                self._corrosion_index = 2  # CORROSION ALERT
                self._corrosion_sensor.heater = True  # turn heater ON
                self._heater_on = True
            elif self._temp_c <= self._dew_c + 5:
                self._corrosion_index = 1  # CORROSION WARNING
                self._corrosion_sensor.heater = False  # turn heater OFF
                self._heater_on = False
            else:
                self._corrosion_index = 0  # NORMAL
                self._corrosion_sensor.heater = False  # turn heater OFF
                self._heater_on = False
        return