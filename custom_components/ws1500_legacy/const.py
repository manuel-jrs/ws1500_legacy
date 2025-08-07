"""Constants for WS1500 Legacy integration."""

# Domain
DOMAIN = "ws1500_legacy"

# Default values
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_TIMEOUT = 10
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 3600

# URLs and endpoints
LIVEDATA_ENDPOINT = "/livedata.htm"
STATION_ENDPOINT = "/station.htm"
REBOOT_ENDPOINT = "/msgreboot.htm"

# Device information
DEVICE_MANUFACTURER = "Fine Offset"
DEVICE_MODEL = "WS1500"
DEVICE_SW_VERSION = "Legacy"
DEVICE_SUGGESTED_AREA = "Garden"

# Sensor data mapping - key to regex pattern
SENSOR_DATA_MAPPING = {
    "wind_direction": 'name="windir"[^>]*value="([0-9]+)"',
    "wind_speed": 'name="avgwind"[^>]*value="([-0-9\\.]+)"',
    "wind_gust": 'name="gustspeed"[^>]*value="([-0-9\\.]+)"',
    "max_daily_gust": 'name="dailygust"[^>]*value="([-0-9\\.]+)"',
    "out_temp": 'name="outTemp"[^>]*value="([-0-9\\.]+)"',
    "out_humidity": 'name="outHumi"[^>]*value="([0-9]+)"',
    "solar_rad": 'name="solarrad"[^>]*value="([-0-9\\.]+)"',
    "uvi": 'name="uvi"[^>]*value="([0-9]+)"',
    "hourly_rain": 'name="rainofhourly"[^>]*value="([-0-9\\.]+)"',
    "daily_rain": 'name="rainofdaily"[^>]*value="([-0-9\\.]+)"',
    "weekly_rain": 'name="rainofweekly"[^>]*value="([-0-9\\.]+)"',
    "monthly_rain": 'name="rainofmonthly"[^>]*value="([-0-9\\.]+)"',
    "yearly_rain": 'name="rainofyearly"[^>]*value="([-0-9\\.]+)"',
}

# Unit mappings from device settings
WIND_UNITS = {0: "m/s", 1: "km/h", 2: "ft/s", 3: "bft", 4: "mph", 5: "knot"}
RAIN_UNITS = {0: "mm", 1: "in"}
PRESSURE_UNITS = {0: "hPa", 1: "inHg", 2: "mmHg"}
TEMP_UNITS = {0: "°C", 1: "°F"}
SOLAR_UNITS = {0: "lux", 1: "W/m²", 2: "fc"}

# Regex patterns for station settings - compiled for performance
TIMEZONE_PATTERN = r'name="timezone"[^>]*value="([-0-9\.]+)"'
DST_PATTERN = r'name="dst".*?<option value="(\d+)"[^>]*selected'
WIND_UNIT_PATTERN = r'name="unit_Wind".*?<option value="(\d+)"[^>]*selected'
RAIN_UNIT_PATTERN = r'name="u_Rainfall".*?<option value="(\d+)"[^>]*selected'
PRESSURE_UNIT_PATTERN = r'name="unit_Pressure".*?<option value="(\d+)"[^>]*selected'
TEMP_UNIT_PATTERN = r'name="u_Temperature".*?<option value="(\d+)"[^>]*selected'
SOLAR_UNIT_PATTERN = r'name="unit_Solar".*?<option value="(\d+)"[^>]*selected'

# Cache settings
CACHE_DURATION = 30  # seconds to cache station settings
DATA_CACHE_DURATION = 5  # seconds to cache sensor data
