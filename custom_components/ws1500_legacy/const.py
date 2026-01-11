"""Constants for WS1500 Legacy integration."""

from typing import Final

# =============================================================================
# Domain and Integration Info
# =============================================================================
DOMAIN: Final = "ws1500_legacy"
INTEGRATION_NAME: Final = "Ambient Weather WS1500 Legacy"

# =============================================================================
# Device Information
# =============================================================================
DEVICE_MANUFACTURER: Final = "Fine Offset"
DEVICE_MODEL: Final = "WS1500"
DEVICE_SW_VERSION: Final = "Legacy"
DEVICE_SUGGESTED_AREA: Final = "Garden"
DEVICE_NAME_TEMPLATE: Final = "WS1500 Weather Station ({host})"

# =============================================================================
# Configuration Defaults
# =============================================================================
DEFAULT_SCAN_INTERVAL: Final = 60
DEFAULT_TIMEOUT: Final = 10
MIN_SCAN_INTERVAL: Final = 10
MAX_SCAN_INTERVAL: Final = 3600

# =============================================================================
# URLs and Endpoints
# =============================================================================
LIVEDATA_ENDPOINT: Final = "/livedata.htm"
STATION_ENDPOINT: Final = "/station.htm"
REBOOT_ENDPOINT: Final = "/msgreboot.htm"

# =============================================================================
# Cache Settings
# =============================================================================
CACHE_DURATION: Final = 30  # seconds to cache station settings
DATA_CACHE_DURATION: Final = 5  # seconds to cache sensor data

# =============================================================================
# Sensor Entity Prefix
# =============================================================================
ENTITY_ID_PREFIX: Final = "ws1500_legacy"
SENSOR_NAME_PREFIX: Final = "WS1500"

# =============================================================================
# Unit Mappings from Device Settings (device value -> unit string)
# =============================================================================
WIND_UNITS: Final = {0: "m/s", 1: "km/h", 2: "ft/s", 3: "bft", 4: "mph", 5: "knot"}
RAIN_UNITS: Final = {0: "mm", 1: "in"}
PRESSURE_UNITS: Final = {0: "hPa", 1: "inHg", 2: "mmHg"}
TEMP_UNITS: Final = {0: "°C", 1: "°F"}
SOLAR_UNITS: Final = {0: "lux", 1: "W/m²", 2: "fc"}

# =============================================================================
# Unit Conversion Functions (to metric/SI units)
# =============================================================================

def convert_temperature(value: float, from_unit: str) -> float:
    """Convert temperature to Celsius."""
    if value is None:
        return None
    if from_unit == "°F":
        return (value - 32) * 5 / 9
    return value  # Already Celsius


def convert_wind_speed(value: float, from_unit: str) -> float:
    """Convert wind speed to km/h."""
    if value is None:
        return None
    conversions = {
        "m/s": lambda v: v * 3.6,
        "ft/s": lambda v: v * 1.09728,
        "mph": lambda v: v * 1.60934,
        "knot": lambda v: v * 1.852,
        "bft": lambda v: v,  # Beaufort scale, keep as-is
        "km/h": lambda v: v,
    }
    converter = conversions.get(from_unit, lambda v: v)
    return converter(value)


def convert_rain(value: float, from_unit: str) -> float:
    """Convert rain to mm."""
    if value is None:
        return None
    if from_unit == "in":
        return value * 25.4
    return value  # Already mm


def convert_pressure(value: float, from_unit: str) -> float:
    """Convert pressure to hPa."""
    if value is None:
        return None
    conversions = {
        "inHg": lambda v: v * 33.8639,
        "mmHg": lambda v: v * 1.33322,
        "hPa": lambda v: v,
    }
    converter = conversions.get(from_unit, lambda v: v)
    return converter(value)


def convert_solar(value: float, from_unit: str) -> float:
    """Convert solar radiation to W/m²."""
    if value is None:
        return None
    conversions = {
        "lux": lambda v: v * 0.0079,  # Approximate conversion
        "fc": lambda v: v * 0.0929 * 0.0079,  # fc -> lux -> W/m²
        "W/m²": lambda v: v,
    }
    converter = conversions.get(from_unit, lambda v: v)
    return converter(value)


# =============================================================================
# Sensor Categories for Unit Conversion
# =============================================================================
TEMPERATURE_SENSORS: Final = frozenset({"out_temp", "in_temp"})
WIND_SENSORS: Final = frozenset({"wind_speed", "wind_gust", "max_daily_gust"})
RAIN_SENSORS: Final = frozenset({
    "hourly_rain", "event_rain", "daily_rain",
    "weekly_rain", "monthly_rain", "yearly_rain"
})
PRESSURE_SENSORS: Final = frozenset({"abs_pressure", "rel_pressure"})
SOLAR_SENSORS: Final = frozenset({"solar_rad"})

# =============================================================================
# Sensor Data Mapping - key to regex pattern
# =============================================================================
SENSOR_DATA_MAPPING: Final = {
    # Wind sensors (always available)
    "wind_direction": 'name="windir"[^>]*value="([0-9]+)"',
    "wind_speed": 'name="avgwind"[^>]*value="([-0-9\\.]+)"',
    "wind_gust": 'name="gustspeed"[^>]*value="([-0-9\\.]+)"',
    "max_daily_gust": 'name="dailygust"[^>]*value="([-0-9\\.]+)"',

    # Outdoor temperature and humidity (always available)
    "out_temp": 'name="outTemp"[^>]*value="([-0-9\\.]+)"',
    "out_humidity": 'name="outHumi"[^>]*value="([0-9]+)"',

    # Solar and UV (available on most WS1500)
    "solar_rad": 'name="solarrad"[^>]*value="([-0-9\\.]+)"',
    "uvi": 'name="uvi"[^>]*value="([0-9]+)"',

    # Rain sensors (available on most WS1500)
    "hourly_rain": 'name="rainofhourly"[^>]*value="([-0-9\\.]+)"',
    "event_rain": 'name="eventrain"[^>]*value="([-0-9\\.]+)"',
    "daily_rain": 'name="rainofdaily"[^>]*value="([-0-9\\.]+)"',
    "weekly_rain": 'name="rainofweekly"[^>]*value="([-0-9\\.]+)"',
    "monthly_rain": 'name="rainofmonthly"[^>]*value="([-0-9\\.]+)"',
    "yearly_rain": 'name="rainofyearly"[^>]*value="([-0-9\\.]+)"',

    # Optional sensors (may not be installed on all devices)
    "in_temp": 'name="inTemp"[^>]*value="([-0-9\\.]+)"',
    "in_humidity": 'name="inHumi"[^>]*value="([^"]*)"',
    "abs_pressure": 'name="AbsPress"[^>]*value="([-0-9\\.]+)"',
    "rel_pressure": 'name="RelPress"[^>]*value="([-0-9\\.]+)"',
    "pm25_indoor": 'name="pm25in"[^>]*value="([-0-9\\.]+)"',
    "pm25_outdoor": 'name="pm25out"[^>]*value="([-0-9\\.]+)"',
}

# =============================================================================
# Regex Patterns for Station Settings
# =============================================================================
TIMEZONE_PATTERN: Final = r'name="timezone"[^>]*value="([-0-9\.]+)"'
DST_PATTERN: Final = r'name="dst".*?<option value="(\d+)"[^>]*selected'
WIND_UNIT_PATTERN: Final = r'name="unit_Wind".*?<option value="(\d+)"[^>]*selected'
RAIN_UNIT_PATTERN: Final = r'name="u_Rainfall".*?<option value="(\d+)"[^>]*selected'
PRESSURE_UNIT_PATTERN: Final = r'name="unit_Pressure".*?<option value="(\d+)"[^>]*selected'
TEMP_UNIT_PATTERN: Final = r'name="u_Temperature".*?<option value="(\d+)"[^>]*selected'
SOLAR_UNIT_PATTERN: Final = r'name="unit_Solar".*?<option value="(\d+)"[^>]*selected'

# =============================================================================
# Info Sensor Patterns
# =============================================================================
INFO_SENSOR_MAPPING: Final = {
    "outdoor1_id": 'name="Outdoor1ID"[^>]*value="([^"]*)"',
    "outdoor1_battery": 'name="outBattSta1"[^>]*value="([^"]*)"',
    "current_time": 'name="CurrTime"[^>]*value="([^"]*)"',
}

# =============================================================================
# Values Indicating Sensor Not Installed/Unavailable
# =============================================================================
UNAVAILABLE_VALUES: Final = frozenset(["----", "--", "--.-", "0x--", "- -"])

# =============================================================================
# Default Station Data (when fetch fails)
# =============================================================================
DEFAULT_STATION_DATA: Final = {
    "timezone": "unknown",
    "dst": "unknown",
    "wind_unit": "km/h",
    "rain_unit": "mm",
    "pressure_unit": "hPa",
    "temp_unit": "°C",
    "solar_unit": "W/m²",
}
