# Workstation Corrosion Monitor
# Copyright 2018, 2019, 2020, 20221, 2022 by JG for Cedar Grove Maker Studios
#
# corrosion_code.py 2022-07-08 v4.2

import time
import board
from digitalio import DigitalInOut, Direction
from simpleio import map_range
from corrosion_display import CorrosionDisplay
from corrosion_sensors import CorrosionTempHumid, CorrosionLight, CorrosionTemp

# fmt: off
# Adafruit IO Feed Names
SHOP_TEMP     = "shop.int-temperature"      # workshop temperature   (F)
SHOP_HUMID    = "shop.int-humidity"         # workshop humidity      (%)
SHOP_DP       = "shop.int-dewpoint"         # workshop dew point     (F)
SHOP_CORR     = "shop.int-corrosion-index"  # workshop corrosion indicator (0, 1, 2)
SHOP_PCB_TEMP = "shop.int-pcb-temperature"  # workshop device PCB temperature (F)

# Sensor and cluster sending delays
AIO_CLUSTER_DELAY  = 10  # minutes
AIO_CLUSTER_OFFSET =  5  # minutes
AIO_SENSOR_DELAY   =  2  # seconds
DUAL_SENSOR_DELAY  =  3  # seconds

# Cooling fan controls
FAN_ON_DISP_BRIGHTNESS =  0  # Display brightness when fan is running
FAN_ON_TRESHOLD_F      = 80  # Degrees Farenheit

# Gesture controls
GESTURE_DURATION = 10            # Backlight "on" duration after gesture (seconds)
GESTURE_DETECT_THRESHOLD = 0.90  # Detection threshold compared to ambient light

# Instantiate Corrosion Monitor classes
sensor = CorrosionTempHumid(sensor="SHT31D")
light  = CorrosionLight()
pcb    = CorrosionTemp()
disp   = CorrosionDisplay(brightness=0.75)

fan           = DigitalInOut(board.D4)  # D4 Stemma 3-pin connector
fan.direction = Direction.OUTPUT
fan.value     = False  # Initialize with fan off
# fmt: on

if disp.sd_card:
    print("SD card present")
else:
    print("NO SD card")

# fmt: off
while_loop_startup_init   = True   # Forces first pass through loop sections
previous_sensor_heater_on = False  # The historical sensor heater state
backlight_timer           = None   # Used for timing the backlight
backlight_on              = False  # The backlight state
clock_tick                = False  # The clock tick indicator state

aio_feed_write = True  # Enable feeds to AIO
sd_card_write  = True  # Enable sd card logging
# fmt: on

while True:
    now = time.localtime()
    format_str = "%04d-%02d-%02d, %02d:%02d:%02d"
    time_str = format_str % (now[0], now[1], now[2], now[3], now[4], now[5])

    disp.clock_tick = not disp.clock_tick  # Change the on-screen tick indicator

    # Monitor the light level; look for a gesture and adjust brightness
    light_level, ambient_level = light.raw  # Get light sensor raw value (0 to 65535)
    brightness_ratio = light_level / ambient_level
    if not backlight_on:
        # Check for gesture; reading less than threshold of brightness ratio
        if brightness_ratio < GESTURE_DETECT_THRESHOLD:
            print(f"GESTURE DETECTED {time_str:16s}")
            backlight_timer = time.monotonic()
            backlight_on = True
        elif brightness_ratio > 2 - GESTURE_DETECT_THRESHOLD:
            # Ambient light level increased; recalibrate ambient level
            print("Recalibrate light sensor ambient level")
            light.ambient_calibrate()  # Update light sensor ambient level value
    if backlight_on:
        # Set display brightness to maximum regardless of cooling fan state
        disp.brightness = 1.0
        # After GESTURE_DURATION seconds, dim the backlight
        if (time.monotonic() - backlight_timer) > GESTURE_DURATION:
            print(f"GESTURE TIMEOUT  {time_str:16s}")
            backlight_on = False
            print("Recalibrate light sensor ambient level")
            light.ambient_calibrate()  # Update light sensor ambient level value
    else:
        # Set the idle backlight level when not responding to a gesture
        if fan.value:
            # Drop the brightness level dramatically until things cool down
            disp.brightness = FAN_ON_DISP_BRIGHTNESS
        else:
            # Set the display to a slightly dimmed level based on ambient level
            disp.brightness = map_range(ambient_level / 65535, 0.010, 0.750, 0.010, 0.5)

    # Do something every minute or when first starting the while loop
    if now.tm_sec == 0 or while_loop_startup_init:
        disp.show()  # Update clock display

        # Acquire and condition sensor data
        disp.sensor_icon = True
        disp.clock_tick = False
        sensor.read()  # Read temperature, humidity, dew_point, and corrosion_index
        temp_c, temp_f = sensor.temperature  # Get temperature values
        humid = sensor.humidity  # Get humidity value
        dew_pt_c, dew_pt_f = sensor.dew_point  # Get dew point values
        corrosion_index = sensor.corrosion_index  # Get corrosion index value

        pcb.read()  # Refresh the PCB temperature sensor
        pcb_c, pcb_f = pcb.temperature

        if pcb_f > FAN_ON_TRESHOLD_F:  # turn on cooling fan if needed
            fan.value = True
        else:
            fan.value = False

        # Send sensor values to the display
        disp.temperature = temp_c
        disp.humidity = humid
        disp.corrosion_status = corrosion_index
        disp.pcb_temperature = pcb_c

        # Display changed sensor heater status once
        if sensor.heater_on != previous_sensor_heater_on:
            if sensor.heater_on:
                disp.alert("Sensor heater: ON")
            else:
                disp.alert("Sensor heater: OFF")
        previous_sensor_heater_on = sensor.heater_on

        # Print temperature values to REPL
        print(
            "Fahrenheit: %16s, %3.1f, %3.1f, %3.1f"
            % (time_str, temp_f, humid, dew_pt_f)
        )
        print(
            "Celsius:    %16s, %3.1f, %3.1f, %3.1f"
            % (time_str, temp_c, humid, dew_pt_c)
        )

        disp.show(refresh=while_loop_startup_init)  # Enable the display
        while_loop_startup_init = False  # Reset the while loop startup flag

    # Do something every AIO_CLUSTER_DELAY starting at AIO_CLUSTER_OFFSET
    #   minutes past the hour
    if now.tm_min % AIO_CLUSTER_DELAY == AIO_CLUSTER_OFFSET and now.tm_sec < 10:
        # Send sensor data to the SD card and AIO
        if sd_card_write:
            sd_data_record = "%16s, %3.1f, %3.1f, %3.1f" % (
                time_str,
                temp_f,
                humid,
                dew_pt_f,
            )
            print("SD: " + sd_data_record)
            if disp.sd_card:
                disp.sd_icon = True
                log_file = open("/sd/logfile.csv", "a")
                log_file.write(sd_data_record)
                log_file.close()
                time.sleep(1)
                disp.sd_icon = False
            else:
                disp.alert("-- NO SD CARD")

        # Send sensor data to Adafruit IO
        if aio_feed_write:
            disp.show()  # Update the display
            # Send temperature to AIO feed
            if temp_f != None:
                disp._temperature.color = disp.BLUE
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_TEMP, temp_f)
                disp.network_icon = False
                time.sleep(AIO_SENSOR_DELAY)
            disp._temperature.color = disp.WHITE

            disp.show()  # Update the display
            # Send humidity to AIO feed
            if humid != None:
                disp._humidity.color = disp.BLUE
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_HUMID, humid)
                disp.network_icon = False
                time.sleep(AIO_SENSOR_DELAY)
            disp._humidity.color = disp.WHITE

            disp.show()  # Update the display
            # Send dew point temperature to AIO feed
            if dew_pt_f != None:
                disp._dew_point.color = disp.BLUE
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_DP, dew_pt_f)
                disp.network_icon = False
                time.sleep(AIO_SENSOR_DELAY)
            disp._dew_point.color = disp.WHITE

            disp.show()  # Update the display
            # Send PyPortal PCB temperature to AIO feed
            if pcb_f != None:
                disp._pcb_temp.color = disp.BLUE
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_PCB_TEMP, pcb_f)
                disp.network_icon = False
                time.sleep(AIO_SENSOR_DELAY)
            disp._pcb_temp.color = disp.CYAN

            disp.show()  # Update the display
            # Send corrosion index value to AIO feed
            if not None in (temp_f, dew_pt_f):
                disp._status_icon.fill = disp.BLUE
                disp._status.color = None
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_CORR, corrosion_index)
                disp.network_icon = False
                disp.corrosion_status = corrosion_index  # refresh status
                time.sleep(AIO_SENSOR_DELAY)

            disp.show()  # Update the display

            try:
                # Update the local time from AIO time service
                disp.network_icon = True
                disp.clock_icon = True
                disp.clock_tick = False
                disp.pyportal.get_local_time()
                disp.clock_icon = False
                disp.network_icon = False
                now = time.localtime()
                time_str = format_str % (now[0], now[1], now[2], now[3], now[4], now[5])
                print("Time updated from AIO:", time_str)
            except (ValueError, RuntimeError) as e:
                disp.alert("-- Get time error -" + str(e))

        disp.show()  # Update the display
        disp.alert()  # Clear error notifications

    # Wait one second before looping (blocking)
    prev_sec = now.tm_sec
    while now.tm_sec == prev_sec:
        now = time.localtime()
