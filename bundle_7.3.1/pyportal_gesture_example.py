# PyPortal Gesture Detector Example
# Copyright 2022 by JG for Cedar Grove Maker Studios
#
# pyportal_gesture_example.py 2022-07-12 v4.0712

import board
from analogio import AnalogIn

# Instantiate light sensor input
light_sensor = AnalogIn(board.LIGHT)

# Gesture detection threshold: foreground to background ratio
GESTURE_DETECT_THRESHOLD = 0.90


def read_foreground(background, samples=2000):
    """Read and average sensor values. Adjust the background baseline
    slightly with the new reading. A high samples value will reduce sensitivity
    to flickering light sources but will proportionally increase acquisition
    latency. Background level is adjusted slightly each time the foreground
    level is read. A maximum reading is equivalent to approximately 1100 Lux."""
    foreground = 0
    for i in range(samples):
        foreground = foreground + light_sensor.value
    foreground = foreground / samples
    background = (0.99 * background) + (0.01 * foreground)
    # Calculate foreground to background brightness ratio
    ratio = foreground / background
    return foreground, background, ratio

def read_background(samples=2000):
    """Read and average sensor values to establish the background light
    level. A high samples value will reduce sensitivity to flickering light
    sources but will proportionally increase acquisition latency. """
    background = 0
    for i in range(samples):
        background = background + light_sensor.value
    background = background / samples
    return background


# Establish baseline background value
background_level = read_background()

while True:
    # Monitor the light level; look for a gesture.
    _, background_level, brightness_ratio = read_foreground(background_level)

    # Check for gesture; reading less than threshold of brightness ratio
    if brightness_ratio < GESTURE_DETECT_THRESHOLD:
        print(f"GESTURE DETECTED  {brightness_ratio:6.3f}")
    elif brightness_ratio > 2 - GESTURE_DETECT_THRESHOLD:
        # Background light level increased; refresh background measurement
        print("Refresh light sensor background measurement")
        background_level = read_background()
