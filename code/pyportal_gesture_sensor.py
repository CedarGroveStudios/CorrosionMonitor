# PyPortal Gesture Detector Using Light Sensor
# Copyright 2018, 2019, 2020, 2021, 2022 by JG for Cedar Grove Maker Studios
#
# pyportal_gesture_sensor.py 2022-07-11 v4.0711

import time
import board
from analogio import AnalogIn


class PyPortalLightSensor:
    """A simple class for the PyPortal's integral light sensor that measures
    raw background and foreground levels. Ambient level is a 1000-count average;
    forground reading is a 250-count average. Ambient level is adjusted slightly
    each time a foreground reading is taken."""

    def __init__(self):
        """Instantiate the light sensor and measure the ambient light level."""
        self._sensor = AnalogIn(board.LIGHT)
        self.ambient_calibrate()

    @property
    def raw(self):
        """Acquire the current and ambient raw light sensor value."""
        self._read_sensor_value()
        return self._raw, self._ambient

    def _read_sensor_value(self):
        """Read and average 250 sensor values. Adjust the ambient baseline
        slightly with the new reading."""
        self._raw = 0
        for i in range(250):
            self._raw = self._raw + self._sensor.value
        self._raw = self._raw / 250
        self._ambient = (0.99 * self._ambient) + (0.01 * self._raw)

    def ambient_calibrate(self):
        """Read and average 1000 sensor valules to establish the ambient light
        level."""
        self._ambient = 0
        for i in range(1000):
            self._ambient = self._ambient + self._sensor.value
        self._ambient = self._ambient / 1000


# Gesture controls
GESTURE_DURATION = 10            # Gesture "on" duration after detection (seconds)
GESTURE_DETECT_THRESHOLD = 0.90  # Detection threshold compared to ambient light

# Instantiate Corrosion Monitor classes
light_sensor = PyPortalLightSensor()

gesture_timer    = None   # Used for timing the gesture response duration
gesture_detected = False  # The gesture detection state

while True:
    # Monitor the light level; look for a gesture.
    # Get light sensor raw value (0 to 65535)
    light_level, ambient_level = light_sensor.raw
    # Calculate foreground to background ratio
    brightness_ratio = light_level / ambient_level

    if not gesture_detected:
        # Check for gesture; reading less than threshold of brightness ratio
        if brightness_ratio < GESTURE_DETECT_THRESHOLD:
            print(f"GESTURE DETECTED {time_str:16s}")
            gesture_timer = time.monotonic()
            gesture_detected = True
        elif brightness_ratio > 2 - GESTURE_DETECT_THRESHOLD:
            # Ambient light level increased; recalibrate ambient level
            print("Recalibrate light sensor ambient level")
            light_sensor.ambient_calibrate()

    if gesture_detected:
        # Gesture "on" action method goes here
        # After GESTURE_DURATION seconds
        if (time.monotonic() - backlight_timer) > GESTURE_DURATION:
            print(f"GESTURE TIMEOUT  {time_str:16s}")
            gesture_detected = False
            print("Recalibrate light sensor ambient level")
            light.ambient_calibrate()  # Update light sensor ambient level value
    else:
        # Gesture "off" action method goes here
        pass
