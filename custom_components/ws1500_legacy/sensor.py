import logging
import re
import requests
from datetime import datetime
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_RESOURCE, CONF_SCAN_INTERVAL, CONF_HOST
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

SENSOR_DEFS = [
    # name, unique_id, regex, unit, device_class, state_class, icon
    ("Wind Direction", "wind_direction", 'name="windir"[^>]*value="([0-9]+)"', "°", "wind_direction", "measurement", "mdi:compass-outline"),
    ("Wind Speed", "wind_speed", 'name="avgwind"[^>]*value="([-0-9\\.]+)"', "km/h", "wind_speed", "measurement", "mdi:weather-windy"),
    ("Wind Gust", "wind_gust", 'name="gustspeed"[^>]*value="([-0-9\\.]+)"', "km/h", "wind_speed", "measurement", "mdi:weather-windy-variant"),
    ("Max Daily Gust", "max_daily_gust", 'name="dailygust"[^>]*value="([-0-9\\.]+)"', "km/h", "wind_speed", "total_increasing", "mdi:weather-windy-variant"),
    ("Outdoor Temperature", "out_temp", 'name="outTemp"[^>]*value="([-0-9\\.]+)"', "°C", "temperature", "measurement", "mdi:thermometer"),
    ("Outdoor Humidity", "out_humidity", 'name="outHumi"[^>]*value="([0-9]+)"', "%", "humidity", "measurement", "mdi:water-percent"),
    ("Solar Radiation", "solar_rad", 'name="solarrad"[^>]*value="([-0-9\\.]+)"', "W/m²", "irradiance", "measurement", "mdi:solar-power"),
    ("UV Index", "uvi", 'name="uvi"[^>]*value="([0-9]+)"', "UVI", None, "measurement", "mdi:weather-sunny-alert"),
    ("Hourly Rain", "hourly_rain", 'name="rainofhourly"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation_intensity", "measurement", "mdi:weather-rainy"),
    ("Daily Rain", "daily_rain", 'name="rainofdaily"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation", "total_increasing", "mdi:weather-rainy"),
    ("Weekly Rain", "weekly_rain", 'name="rainofweekly"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation", "total_increasing", "mdi:weather-rainy"),
    ("Monthly Rain", "monthly_rain", 'name="rainofmonthly"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation", "total_increasing", "mdi:weather-rainy"),
    ("Yearly Rain", "yearly_rain", 'name="rainofyearly"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation", "total_increasing", "mdi:weather-rainy"),
    ("Time Zone", "timezone", '', '', None, None, "mdi:clock-outline"),
    ("Daylight Saving", "dst", '', '', None, None, "mdi:weather-sunset"),
    ("Device IP", "device_ip", '', '', None, None, "mdi:ip-network"),
    ("Wind Unit", "wind_unit", '', '', None, None, "mdi:weather-windy"),
    ("Rain Unit", "rain_unit", '', '', None, None, "mdi:weather-rainy"),
    ("Pressure Unit", "pressure_unit", '', '', None, None, "mdi:gauge"),
    ("Temperature Unit", "temp_unit", '', '', None, None, "mdi:thermometer"),
    ("Solar Unit", "solar_unit", '', '', None, None, "mdi:solar-power"),
    ("Last Update", "last_update", '', '', None, None, "mdi:clock-check"),
]

# Unit mappings from device settings
WIND_UNITS = {0: "m/s", 1: "km/h", 2: "ft/s", 3: "bft", 4: "mph", 5: "knot"}
RAIN_UNITS = {0: "mm", 1: "in"}
PRESSURE_UNITS = {0: "hPa", 1: "inHg", 2: "mmHg"}
TEMP_UNITS = {0: "°C", 1: "°F"}
SOLAR_UNITS = {0: "lux", 1: "W/m²", 2: "fc"}

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up WS1500 Legacy platform via YAML."""
    host = config.get(CONF_HOST)
    scan_interval = config.get(CONF_SCAN_INTERVAL, 60)
    resource = f"http://{host}/livedata.htm"
    sensors = [
        WS1500LegacySensor(resource, scan_interval, *sensor_def)
        for sensor_def in SENSOR_DEFS
    ]
    async_add_entities(sensors)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up WS1500 Legacy platform via UI."""
    host = config_entry.data[CONF_HOST]
    scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL, 60)
    resource = f"http://{host}/livedata.htm"
    sensors = [
        WS1500LegacySensor(resource, scan_interval, *sensor_def)
        for sensor_def in SENSOR_DEFS
    ]
    async_add_entities(sensors)

class WS1500LegacySensor(SensorEntity):
    def __init__(self, resource, scan_interval, name, unique_id, regex, unit, device_class, state_class, icon):
        self._resource = resource
        self._scan_interval = scan_interval
        # Use only the English name, translations will be applied automatically
        self._attr_name = name
        self._attr_unique_id = f"ws1500_legacy_{unique_id}"
        self._regex = regex
        self._attr_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        self._state = None

    def update(self):
        try:
            host = self._resource.replace("http://", "").replace("/livedata.htm", "")
            
            if self._unique_id == "ws1500_legacy_device_ip":
                # Show device IP
                self._state = host
                
            elif self._unique_id == "ws1500_legacy_last_update":
                # Show last successful update time
                self._state = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            elif self._unique_id in ["ws1500_legacy_timezone", "ws1500_legacy_dst", 
                                   "ws1500_legacy_wind_unit", "ws1500_legacy_rain_unit", 
                                   "ws1500_legacy_pressure_unit", "ws1500_legacy_temp_unit", 
                                   "ws1500_legacy_solar_unit"]:
                # Special sensors to read device settings from station.htm
                station_url = f"http://{host}/station.htm"
                response = requests.get(station_url, timeout=10)
                if response.status_code == 200:
                    if self._unique_id == "ws1500_legacy_timezone":
                        timezone_match = re.search(r'name="timezone"[^>]*value="([-0-9\.]+)"', response.text)
                        if timezone_match:
                            timezone_value = float(timezone_match.group(1))
                            self._state = f"UTC{timezone_value:+g}"
                        else:
                            self._state = "unknown"
                            
                    elif self._unique_id == "ws1500_legacy_dst":
                        dst_match = re.search(r'name="dst".*?<option value="(\d+)" selected=""', response.text, re.DOTALL)
                        if dst_match:
                            dst_value = int(dst_match.group(1))
                            self._state = "on" if dst_value == 1 else "off"
                        else:
                            self._state = "unknown"
                            
                    elif self._unique_id == "ws1500_legacy_wind_unit":
                        wind_match = re.search(r'name="unit_Wind".*?<option value="(\d+)" selected=""', response.text, re.DOTALL)
                        if wind_match:
                            unit_value = int(wind_match.group(1))
                            self._state = WIND_UNITS.get(unit_value, "unknown")
                        else:
                            self._state = "unknown"
                            
                    elif self._unique_id == "ws1500_legacy_rain_unit":
                        rain_match = re.search(r'name="u_Rainfall".*?<option value="(\d+)" selected=""', response.text, re.DOTALL)
                        if rain_match:
                            unit_value = int(rain_match.group(1))
                            self._state = RAIN_UNITS.get(unit_value, "unknown")
                        else:
                            self._state = "unknown"
                            
                    elif self._unique_id == "ws1500_legacy_pressure_unit":
                        pressure_match = re.search(r'name="unit_Pressure".*?<option value="(\d+)" selected=""', response.text, re.DOTALL)
                        if pressure_match:
                            unit_value = int(pressure_match.group(1))
                            self._state = PRESSURE_UNITS.get(unit_value, "unknown")
                        else:
                            self._state = "unknown"
                            
                    elif self._unique_id == "ws1500_legacy_temp_unit":
                        temp_match = re.search(r'name="u_Temperature".*?<option value="(\d+)" selected=""', response.text, re.DOTALL)
                        if temp_match:
                            unit_value = int(temp_match.group(1))
                            self._state = TEMP_UNITS.get(unit_value, "unknown")
                        else:
                            self._state = "unknown"
                            
                    elif self._unique_id == "ws1500_legacy_solar_unit":
                        solar_match = re.search(r'name="unit_Solar".*?<option value="(\d+)" selected=""', response.text, re.DOTALL)
                        if solar_match:
                            unit_value = int(solar_match.group(1))
                            self._state = SOLAR_UNITS.get(unit_value, "unknown")
                        else:
                            self._state = "unknown"
                else:
                    self._state = None
            else:
                # Normal weather data sensors
                response = requests.get(self._resource, timeout=10)
                if response.status_code == 200:
                    value = response.text
                    m = re.findall(self._regex, value)
                    self._state = m[0] if m else '0'
                else:
                    self._state = None
        except Exception as e:
            _LOGGER.error(f"WS1500 sensor error: {e}")
            self._state = None

    @property
    def state(self):
        return self._state
