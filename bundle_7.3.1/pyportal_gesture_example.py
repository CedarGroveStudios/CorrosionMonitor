# PyPortal Gesture Detector Example
# Copyright 2018, 2019, 2020, 2021, 2022 by JG for Cedar Grove Maker Studios
#
# pyportal_gesture_example.py 2022-07-11 v4.0711

import board
from analogio import AnalogIn


class PyPortalLightSensor:
    """A simplified class for the PyPortal's integral light sensor to measure
    raw background and foreground levels. Background and foreground levels are
    averaged to reduce sensitivity to flickering light sources. Background level
    is adjusted slightly each time the foreground level is read."""

    def __init__(self, foreground_samples=250, background_samples=1000):
        """Instantiate the light sensor and measure the background light level.
        A high samples value will reduce sensitivity to flickering light
        sources but will proportionally increase acquisition latency. Defaults
        to 250 foreground and 1000 background samples."""
        self._sensor = AnalogIn(board.LIGHT)
        self._foreground_samples = foreground_samples
        self._background_samples = background_samples
        self.read_background()

    @property
    def foreground(self):
        """The current forground and background light sensor values."""
        self._read_foreground()
        return self._foreground, self._background

    def _read_foreground(self):
        """Read and average sensor values. Adjust the background baseline
        slightly with the new reading. A maximum reading is equivalent
        to approximately 1100 Lux."""
        self._foreground = 0
        for i in range(self._frg_samples):
            self._foreground = self._foreground + self._sensor.value
        self._foreground = self._foreground / self._foreground_samples
        self._background = (0.99 * self._background) + (0.01 * self._foreground)

    def read_background(self):
        """Read and average sensor values to establish the background light
        level."""
        self._background = 0
        for i in range(self._background_samples):
            self._background = self._background + self._sensor.value
        self._background = self._background / self._background_samples


# Gesture detection threshold: foreground to background ratio
GESTURE_DETECT_THRESHOLD = 0.90

# Instantiate Corrosion Monitor classes
light_sensor = PyPortalLightSensor()

while True:
    # Monitor the light level; look for a gesture.
    foreground_level, background_level = light_sensor.foreground
    # Calculate foreground to background ratio
    brightness_ratio = foreground_level / background_level

    # Check for gesture; reading less than threshold of brightness ratio
    if brightness_ratio < GESTURE_DETECT_THRESHOLD:
        print("GESTURE DETECTED")
    elif brightness_ratio > 2 - GESTURE_DETECT_THRESHOLD:
        # Background light level increased; refresh background measurement
        print("Refresh light sensor background measurement")
        light_sensor.read_background()
