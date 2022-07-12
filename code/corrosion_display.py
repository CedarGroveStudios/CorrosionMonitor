# WorkshopCorrosion Monitor
# Copyright 2018, 2019, 2020, 2021, 2022 by JG for Cedar Grove Maker Studios
#
# corrosion_display.py  2022-07-08 v2.0708

import time
import board
import gc
import displayio
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.roundrect import RoundRect
from adafruit_display_shapes.triangle import Triangle
import adafruit_imageload
from simpleio import map_range

# Temperature Converter Helpers
from cedargrove_unit_converter.temperature import celsius_to_fahrenheit, dew_point

# Import the PyPortal class; includes ESP32 and IO_HTTP client modules
import adafruit_pyportal


class CorrosionDisplay:
    def __init__(
        self,
        scale="F",
        timezone="Pacific",
        hour_24=False,
        sound=False,
        brightness=1.0,
        debug=False,
    ):
        # Input parameters
        self._scale = scale
        self._timezone = timezone
        self._hour_24_12 = hour_24
        self._sound = sound
        self._brightness = brightness

        # Celcius temperature and percent humidity start-up values
        self._temp_c = 0
        self._humid_pct = 0
        self._dew_c = 0
        self._pcb_c = 0

        # Other parameters
        self.PROJECT = "Workshop Corrosion Monitor"
        self.VERSION = "0.1 2020-11-05"

        self._message = ""
        self._clock_tick = True
        self._corrosion_status = 0

        self._weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self._month = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        # Load the text fonts from the fonts folder
        FONT_1 = bitmap_font.load_font("/fonts/OpenSans-9.bdf")
        FONT_2 = bitmap_font.load_font("/fonts/Arial-12.bdf")
        FONT_3 = bitmap_font.load_font("/fonts/Arial-Bold-24.bdf")
        CLOCK_FONT = bitmap_font.load_font("/fonts/Anton-Regular-104.bdf")

        # The board's integral display size
        WIDTH = board.DISPLAY.width  # 320 for PyPortal
        HEIGHT = board.DISPLAY.height  # 240 for PyPortal

        # Set display brightness
        board.DISPLAY.brightness = self._brightness

        # Default colors
        self.BLACK = 0x000000
        self.RED = 0xFF0000
        self.ORANGE = 0xFF8811
        self.YELLOW = 0xFFFF00
        self.GREEN = 0x00FF00
        self.LT_GRN = 0x00BB00
        self.CYAN = 0x00FFFF
        self.BLUE = 0x0000FF
        self.LT_BLUE = 0x000044
        self.VIOLET = 0x9900FF
        self.DK_VIO = 0x110022
        self.WHITE = 0xFFFFFF
        self.GRAY = 0x444455
        self.LCARS_LT_BLU = 0x1B6BA7

        # Get WiFi and account info from secrets.py
        try:
            from secrets import secrets
        except ImportError:
            print("secrets.py file not found")
            raise

        # Adafruit IO account information (uses secrets.py)
        AIO_DATA_SOURCE = "http://wifitest.adafruit.com/testwifi/index.html"
        AIO_USER = secrets["aio_username"]
        AIO_KEY = secrets["aio_key"]
        AIO_DATA_LOC = []

        # Instantiate the PyPortal class
        self.pyportal = adafruit_pyportal.PyPortal(
            url=AIO_DATA_SOURCE,
            json_path=AIO_DATA_LOC,
            status_neopixel=board.NEOPIXEL,
            default_bg="/corrosion_mon_startup.bmp",
        )
        try:
            self.pyportal.get_local_time()
        except (ValueError, RuntimeError) as e:  # ValueError added from quote.py change
            print("Get time: An error occured -", e)

        # Redundantly set brightness via the PyPortal class
        self.pyportal.set_backlight(self._brightness)

        ### Define the display group ###
        self._image_group = displayio.Group()

        # Create a background color fill layer; image_group[0]
        self._color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 2)
        self._color_palette = displayio.Palette(2)
        self._color_palette[0] = self.BLACK
        self._color_palette[1] = self.WHITE

        # Background Graphics; image_group[0]
        self._bkg = open("/corrosion_mon_bkg.bmp", "rb")
        bkg = displayio.OnDiskBitmap(self._bkg)
        try:
            self._background = displayio.TileGrid(
                bkg, pixel_shader=displayio.ColorConverter(), x=0, y=0
            )
        except TypeError:
            self._background = displayio.TileGrid(
                bkg, pixel_shader=displayio.ColorConverter(), position=(0, 0)
            )
        self._image_group.append(self._background)

        ### Define display graphic, label, and value areas
        # Sensor Data Area Title; image_group[1]
        self._title = Label(FONT_1, text="Interior", color=self.CYAN)
        self._title.anchor_point = (0.5, 0.5)
        self._title.anchored_position = (252, 26)
        self._image_group.append(self._title)

        # Temperature; image_group[2]
        self._temperature = Label(FONT_3, text="  0.0" + "°", color=self.WHITE)
        self._temperature.x = 210
        self._temperature.y = 48
        self._image_group.append(self._temperature)

        # Humidity; image_group[3]
        self._humidity = Label(FONT_2, text="  0%", color=self.WHITE)
        self._humidity.x = 210
        self._humidity.y = 74
        self._image_group.append(self._humidity)

        # Dew Point; image_group[4]
        self._dew_point = Label(
            FONT_2,
            text="  0.0" + "°" + self._scale + " Dew",
            color=self.WHITE,
        )
        self._dew_point.x = 210
        self._dew_point.y = 91
        self._image_group.append(self._dew_point)

        # Clock Hour:Min ; image_group[5]
        self._clock_digits = Label(CLOCK_FONT, text="12:00", color=self.WHITE)
        self._clock_digits.anchor_point = (0.5, 0.5)
        self._clock_digits.anchored_position = (198, 170)
        self._image_group.append(self._clock_digits)

        # Weekday, Month, Date, Year; image_group[6]
        self._clock_day_mon_yr = Label(FONT_1, text="Sun  Jan 01, 1970", color=self.WHITE)
        self._clock_day_mon_yr.anchor_point = (0.5, 0.5)
        self._clock_day_mon_yr.anchored_position = (198, 231)
        self._image_group.append(self._clock_day_mon_yr)

        # Project Message Area; image_group[7]
        self._project_message = Label(FONT_1, text="", color=self.YELLOW)
        self._project_message.anchor_point = (0.5, 0.5)
        self._project_message.anchored_position = (158, 106)
        self._image_group.append(self._project_message)

        # Clock Activity Icon Mask; image_group[8]
        self._clock_tick_mask = RoundRect(
            305, 227, 7, 8, 1, fill=self.VIOLET, outline=None, stroke=0
        )
        self._image_group.append(self._clock_tick_mask)

        # Corrosion Status Icon and Text; image_group[10:11]
        self._status_icon = Triangle(
            155, 38, 185, 90, 125, 90, fill=self.RED, outline=None
        )
        self._image_group.append(self._status_icon)

        self._status = Label(FONT_3, text="!", color=None)
        self._status.anchor_point = (0.5, 0.5)
        self._status.anchored_position = (157, 68)
        self._image_group.append(self._status)

        # Temp/Humid Sensor Icon Mask; image_group[12]
        self._sensor_icon_mask = Rect(
            4, 54, 41, 56, fill=self.LCARS_LT_BLU, outline=None, stroke=0
        )
        self._image_group.append(self._sensor_icon_mask)

        # Sensor Heater Icon Mask; image_group[13]
        self._heater_icon_mask = Rect(
            4, 110, 41, 8, fill=self.LCARS_LT_BLU, outline=None, stroke=0
        )
        self._image_group.append(self._heater_icon_mask)

        # Clock Icon Mask; image_group[14]
        self._clock_icon_mask = Rect(
            45, 54, 34, 56, fill=self.LCARS_LT_BLU, outline=None, stroke=0
        )
        self._image_group.append(self._clock_icon_mask)

        # SD Icon Mask; image_group[15]
        self._sd_icon_mask = Rect(
            4, 156, 72, 31, fill=self.LCARS_LT_BLU, outline=None, stroke=0
        )
        self._image_group.append(self._sd_icon_mask)

        # Network Icon Mask; image_group[16]
        self._net_icon_mask = Rect(
            4, 188, 72, 30, fill=self.LCARS_LT_BLU, outline=None, stroke=0
        )
        self._image_group.append(self._net_icon_mask)

        # PCB Temperature; image_group[17]
        self._pcb_temp = Label(FONT_1, text="  0.0" + "°", color=self.CYAN)
        self._pcb_temp.anchor_point = (0.5, 0.5)
        self._pcb_temp.anchored_position = (40, 231)
        self._image_group.append(self._pcb_temp)

        # board.DISPLAY.show(self._image_group)  # Load display
        gc.collect()

        # debug parameters
        self._debug = debug
        if self._debug:
            print("*Init:", self.__class__)
            print("*Init: ", self.__dict__)

    @property
    def temperature(self):
        # Update the Celsius temperature value.
        return self._temp_c

    @temperature.setter
    def temperature(self, temp_c=0):
        self._temp_c = temp_c
        if self._temp_c == None:
            self._temp.text = "None"
            self._dew_c = None
            self._dew.text = "None"
            return
        self._dew_c = self.calculate_dew_point(self._temp_c, self._humid_pct)
        if self._scale == "F":
            self._temperature.text = (
                str(round(celsius_to_fahrenheit(self._temp_c), 1)) + "°"
            )
            if self._dew_c != None:
                self._dew_point.text = (
                    str(round(celsius_to_fahrenheit(self._dew_c), 1)) + "°" + " Dew"
                )
            else:
                self._dew_point.text = "None"
        else:
            self._temperature.text = str(round(self._temp_c, 1)) + "°"
            if self._dew_c != None:
                self._dew_point.text = str(round(self._dew_c, 1)) + "°" + " Dew"
            else:
                self._dew_point.text = "None"

    @property
    def humidity(self):
        # Update the humidity value.
        return self._humid_pct

    @humidity.setter
    def humidity(self, humid_pct=0):
        self._humid_pct = humid_pct
        if self._humid_pct == None:
            self._humidity.text = "None"
            self._dew_c = None
            self._dew_point.text = "None"
            return
        self._humidity.text = str(round(self._humid_pct, 0)) + "%"
        self._dew_c = self.calculate_dew_point(self._temp_c, self._humid_pct)
        if self._dew_c != None:
            if self._scale == "F":
                self._dew_point.text = (
                    str(round(celsius_to_fahrenheit(self._dew_c), 1)) + "°" + " Dew"
                )
            else:
                self._dew_point.text = str(round(self._dew_c, 1)) + "°" + " Dew"
        else:
            self._dew_point.text = "None"

    @property
    def dew_point(self):
        # The Celsius dew point temperature value.
        return self._dew_c

    @property
    def pcb_temperature(self):
        # The Celsius PyPortal PCB temperature value.
        return self._pcb_c

    @pcb_temperature.setter
    def pcb_temperature(self, pcb_c=0):
        self._pcb_c = pcb_c
        if self._pcb_c == None:
            self._pcb_temp.text = "None"
            return
        if self._scale == "F":
            self._pcb_temp.text = (
                str(round(celsius_to_fahrenheit(self._pcb_c), 1)) + "°"
            )
        else:
            self._pcb_temp.text = str(round(self._pcb_c, 1)) + "°"

    @property
    def message(self):
        # Update the clock's message text. Default is a blank message.
        return self._project_message.text

    @message.setter
    def message(self, text=""):
        if text == None:
            text = ""
        self._message = text[:20]
        print("MESSAGE: " + self._message)

    @property
    def zone(self):
        # The clock's time zone. Default is Pacific.
        return self._timezone

    @zone.setter
    def zone(self, timezone="Pacific"):
        if timezone == None:
            timezone = ""
        self._timezone = timezone

    @property
    def sound(self):
        # Sound is activated. Default is no sound (False).
        return self._sound

    @sound.setter
    def sound(self, sound=False):
        if sound == None:
            sound = False
        self._sound = sound

    @property
    def brightness(self):
        # Display brightness (0 - 1.0). Default is full brightness (1.0).
        return self._brightness

    @brightness.setter
    def brightness(self, brightness=1.0):
        if brightness == None:
            return
        self._brightness = brightness
        board.DISPLAY.brightness = self._brightness

    @property
    def corrosion_status(self):
        return self._corrosion_status

    @corrosion_status.setter
    def corrosion_status(self, corr_status=0):
        if corr_status == None:
            self._status_mask.fill = None
            return
        # Display the corrosion status. Default is no corrosion potential (0 = GREEN).
        self._corrosion_status = corr_status
        if self._corrosion_status == 0:
            self._status_icon.fill = self.LT_GRN
            self._status.color = None
            self.alert("NORMAL")
            self._heater_icon_mask.fill = self.LCARS_LT_BLU
            self._sensor_icon_mask.fill = self.LCARS_LT_BLU
        elif self._corrosion_status == 1:
            self._status_icon.fill = self.YELLOW
            self._status.color = self.RED
            self.alert("CORROSION WARNING")
            self._heater_icon_mask.fill = self.LCARS_LT_BLU
            self._sensor_icon_mask.fill = self.LCARS_LT_BLU
        elif self._corrosion_status == 2:
            self._status_icon.fill = self.RED
            self._status.color = self.BLACK
            self.alert("CORROSION ALERT")
            self._heater_icon_mask.fill = None
            self._sensor_icon_mask.fill = None

    @property
    def clock_tick(self):
        # Display the ticking indicator.
        return self._clock_tick

    @clock_tick.setter
    def clock_tick(self, state=True):
        if state == None:
            state = True
        # Display the clock state indicator. Default is display state indicator (True).
        self._clock_tick = state
        if self._clock_tick:
            self._clock_tick_mask.fill = self.ORANGE
        else:
            self._clock_tick_mask.fill = None

    @property
    def clock_icon(self):
        if self._clock_icon_mask.fill == None:
            return True
        else:
            return False

    @clock_icon.setter
    def clock_icon(self, clock_icon="False"):
        if clock_icon == None:
            clock_icon = False
        # Reveals the icon. Default is icon not displayed.
        if clock_icon:
            self._clock_icon_mask.fill = None
        else:
            self._clock_icon_mask.fill = self.LCARS_LT_BLU
        return

    @property
    def sensor_icon(self):
        if self._sensor_icon_mask.fill == None:
            return True
        else:
            return False

    @sensor_icon.setter
    def sensor_icon(self, sensor_icon="False"):
        if sensor_icon == None:
            sensor_icon = False
        # Reveals the icon. Default is icon not displayed.
        if sensor_icon:
            self._sensor_icon_mask.fill = None
        else:
            self._sensor_icon_mask.fill = self.LCARS_LT_BLU
        return

    @property
    def heater_icon(self):
        if self._heater_icon_mask.fill == None:
            return True
        else:
            return False

    @heater_icon.setter
    def heater_icon(self, heater_icon="False"):
        if heater_icon == None:
            heater_icon = False
        # Reveals the icon. Default is icon not displayed.
        if heater_icon:
            self._heater_icon_mask.fill = None
            self._sensor_icon_mask.fill = None
        else:
            self._heater_icon_mask.fill = self.LCARS_LT_BLU
            self._sensor_icon_mask.fill = self.LCARS_LT_BLU
        return

    @property
    def sd_icon(self):
        if self._sd_icon_mask.fill == None:
            return True
        else:
            return False

    @sd_icon.setter
    def sd_icon(self, sd_icon="False"):
        if sd_icon == None:
            sd_icon = False
        # Reveals the icon. Default is icon not displayed.
        if sd_icon:
            self._sd_icon_mask.fill = None
        else:
            self._sd_icon_mask.fill = self.LCARS_LT_BLU
        return

    @property
    def network_icon(self):
        if self._net_icon_mask.fill == None:
            return True
        else:
            return False

    @network_icon.setter
    def network_icon(self, net_icon="False"):
        if net_icon == None:
            net_icon = False
        # Reveals the icon. Default is icon not displayed.
        if net_icon:
            self._net_icon_mask.fill = None
        else:
            self._net_icon_mask.fill = self.LCARS_LT_BLU
        return

    @property
    def sd_card(self):
        # confirm that SD card is inserted
        if self.pyportal.sd_check():  # confirm that SD card is inserted
            self._sd_icon_mask.fill = None
            time.sleep(0.5)
            self._sd_icon_mask.fill = self.LCARS_LT_BLU
            return True
        return False

    def calculate_dew_point(self, t_c, h):
        # Check for None values and return calculated value or None
        if t_c == None or h == None:
            return None
        return dew_point(t_c, h)

    def alert(self, text=""):
        # Place alert message in clock message area. Default is the previous message.
        self._msg_text = text[:20]
        if self._msg_text == "" or self._msg_text == None:
            self._msg_text = ""
            self._project_message.text = self._message
        else:
            print("ALERT: " + self._msg_text)
            self._project_message.color = self.RED
            self._project_message.text = self._msg_text
            time.sleep(0.1)
            # self.panel.play_tone(880, 0.100)  # A5
            self._project_message.color = self.YELLOW
            time.sleep(0.1)
            # self.panel.play_tone(880, 0.100)  # A5
            self._project_message.color = self.RED
            time.sleep(0.1)
            # self.panel.play_tone(880, 0.100)  # A5
            self._project_message.color = self.YELLOW
            time.sleep(0.5)
            self._project_message.color = None
        return

    def show(self, refresh=False):
        # Display time and refresh display. The primary function of this class.
        self._datetime = time.localtime()  # xST structured time object

        self._hour = self._datetime.tm_hour  # Format 24-hour or 12-hour output
        if not self._hour_24_12:  # 12-hour clock
            if self._hour >= 12:
                self._hour = self._hour - 12
            if self._hour == 0:  # midnight hour fix
                self._hour = 12

        self._project_message.text = self._message
        self._clock_day_mon_yr.text = (
            self._weekday[self._datetime.tm_wday]
            + "  "
            + self._month[self._datetime.tm_mon - 1]
            + " "
            + "{:02d}".format(self._datetime.tm_mday)
            + ", "
            + "{:04d}".format(self._datetime.tm_year)
        )

        self._clock_digits.text = (
            "{:2d}".format(self._hour) + ":" + "{:02d}".format(self._datetime.tm_min)
        )

        if refresh:
            board.DISPLAY.show(self._image_group)  # Load display
        time.sleep(0.1)  # Allow display to load
        gc.collect()
        return
