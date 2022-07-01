# Workstation Corrosion Monitor Test
# 2021-08-17 v03

import time
import board
from digitalio import DigitalInOut, Direction
from simpleio import map_range
from corrosion_display import CorrosionDisplay
from corrosion_sensors import CorrosionTempHumid, CorrosionLight, CorrosionTemp

# Adafruit IO Feed Names
SHOP_TEMP = "shop.int-temperature"  # workshop temperature   (F)
SHOP_HUMID = "shop.int-humidity"  # workshop humidity      (%)
SHOP_DP = "shop.int-dewpoint"  # workshop dew point     (F)
SHOP_CORR = "shop.int-corrosion-index"  # workshop corrosion indicator (0, 1, 2)
SHOP_PCB_TEMP = "shop.int-pcb-temperature"  # workshop device PCB temperature (F)

# Sensor and cluster sending delays
AIO_CLUSTER_DELAY = 10  # minutes
AIO_CLUSTER_OFFSET = 5  # minutes
AIO_SENSOR_DELAY = 2  # seconds
DUAL_SENSOR_DELAY = 3  # seconds

sensor = CorrosionTempHumid(sensor="SHT31D")
light = CorrosionLight()
pcb = CorrosionTemp()
disp = CorrosionDisplay(brightness=0.75)

fan = DigitalInOut(board.D4)  # Stemma 3-pin connector
fan.direction = Direction.OUTPUT
fan.value = False

if disp.sd_card:
    print("SD card present")
else:
    print("NO SD card")

feed_state_flag = False
startup_init = True
old_sensor_heater_on = False

aio_feed_write = True  # Enable feeds to AIO
sd_card_write = True  # Enable sd card logging

while True:
    now = time.localtime()
    format_str = "%04d-%02d-%02d, %02d:%02d:%02d"
    time_str = format_str % (now[0], now[1], now[2], now[3], now[4], now[5])
    disp.clock_tick = not disp.clock_tick

    lux, avg_lux = light.lux
    if fan.value:
        disp.brightness = 0.05  # lower brightness until things cool down
    else:
        disp.brightness = map_range(avg_lux, 10, 50, 0.1, 1.0)
    # print(lux, avg_lux, disp.brightness)

    if (
        now.tm_sec == 0 or startup_init
    ):  # do something every minute or when first starting
        disp.show()  # update clock display
        # Acquire and condition sensor data
        disp.sensor_icon = True
        disp.clock_tick = False

        sensor.read()  # Read temperature, humidity, dew_point, and corrosion_index
        temp_c, temp_f = sensor.temperature  # Get temperature values
        humid = sensor.humidity  # Get humidity value
        dew_pt_c, dew_pt_f = sensor.dew_point  # Get dew point values
        corrosion_index = sensor.corrosion_index  # Get corrosion index value

        pcb.read()
        pcb_c, pcb_f = pcb.temperature
        if pcb_f > 85:  # turn on cooling fan and dim backlight
            fan.value = True
            disp.brightness = 0.05  # lower brightness
        else:
            fan.value = False
            disp.brightness = map_range(avg_lux, 10, 50, 0.1, 1.0)

        # Send values to the display
        disp.temperature = temp_c
        disp.humidity = humid
        disp.corrosion_status = corrosion_index
        disp.pcb_temperature = pcb_c

        if sensor.heater_on != old_sensor_heater_on:
            if sensor.heater_on:
                disp.alert("Sensor heater: ON")
            else:
                disp.alert("Sensor heater: OFF")
        old_sensor_heater_on = sensor.heater_on

        print(
            "Fahrenheit: %16s, %3.1f, %3.1f, %3.1f"
            % (time_str, temp_f, humid, dew_pt_f)
        )
        print(
            "Celsius:    %16s, %3.1f, %3.1f, %3.1f"
            % (time_str, temp_c, humid, dew_pt_c)
        )

        disp.show(refresh=startup_init)  # enable display
        startup_init = False  # reset startup flag

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

        if aio_feed_write:
            # Send sensor data to Adafruit IO
            disp.show()  # update time
            # Send temperature to AIO feed
            if temp_f != None:
                disp._temperature.color = disp.BLUE
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_TEMP, temp_f)
                disp.network_icon = False
                time.sleep(AIO_SENSOR_DELAY)
            disp._temperature.color = disp.WHITE

            disp.show()  # update time
            # Send humidity to AIO feed
            if humid != None:
                disp._humidity.color = disp.BLUE
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_HUMID, humid)
                disp.network_icon = False
                time.sleep(AIO_SENSOR_DELAY)
            disp._humidity.color = disp.WHITE

            disp.show()  # update time
            # Send dew point temperature to AIO feed
            if dew_pt_f != None:
                disp._dew_point.color = disp.BLUE
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_DP, dew_pt_f)
                disp.network_icon = False
                time.sleep(AIO_SENSOR_DELAY)
            disp._dew_point.color = disp.WHITE

            disp.show()  # update time
            # Send PyPortal PCB temperature to AIO feed
            if pcb_f != None:
                disp._pcb_temp.color = disp.BLUE
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_PCB_TEMP, pcb_f)
                disp.network_icon = False
                time.sleep(AIO_SENSOR_DELAY)
            disp._pcb_temp.color = disp.CYAN

            disp.show()  # update time
            # Send corrosion index value to AIO feed
            if not None in (temp_f, dew_pt_f):
                disp._status_icon.fill = disp.BLUE
                disp._status.color = None
                disp.network_icon = True
                disp.pyportal.push_to_io(SHOP_CORR, corrosion_index)
                disp.network_icon = False
                disp.corrosion_status = corrosion_index  # refresh status
                time.sleep(AIO_SENSOR_DELAY)

            disp.show()  # update time

            try:
                # update local time from AIO time service
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

        disp.show()  # update time
        disp.alert()  # clear error notifications

    # wait a second before looping
    prev_sec = now.tm_sec
    while now.tm_sec == prev_sec:  # wait a second before looping
        now = time.localtime()
