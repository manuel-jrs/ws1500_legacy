"""Support for WS1500 Legacy Weather Station sensors."""

import logging
import re
import requests
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    PERCENTAGE,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

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

# Weather sensor descriptions following Home Assistant standards
SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="wind_direction",
        name="Wind Direction",
        native_unit_of_measurement="°",
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass-outline",
    ),
    SensorEntityDescription(
        key="wind_speed",
        name="Wind Speed",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-windy",
    ),
    SensorEntityDescription(
        key="wind_gust",
        name="Wind Gust",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-windy-variant",
    ),
    SensorEntityDescription(
        key="max_daily_gust",
        name="Max Daily Gust",
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:weather-windy-variant",
    ),
    SensorEntityDescription(
        key="out_temp",
        name="Outdoor Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key="out_humidity",
        name="Outdoor Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-percent",
    ),
    SensorEntityDescription(
        key="solar_rad",
        name="Solar Radiation",
        native_unit_of_measurement="W/m²",
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    SensorEntityDescription(
        key="uvi",
        name="UV Index",
        native_unit_of_measurement="UVI",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny-alert",
    ),
    SensorEntityDescription(
        key="hourly_rain",
        name="Hourly Rain",
        native_unit_of_measurement="mm",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-rainy",
    ),
    SensorEntityDescription(
        key="daily_rain",
        name="Daily Rain",
        native_unit_of_measurement="mm",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:weather-rainy",
    ),
    SensorEntityDescription(
        key="weekly_rain",
        name="Weekly Rain",
        native_unit_of_measurement="mm",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:weather-rainy",
    ),
    SensorEntityDescription(
        key="monthly_rain",
        name="Monthly Rain",
        native_unit_of_measurement="mm",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:weather-rainy",
    ),
    SensorEntityDescription(
        key="yearly_rain",
        name="Yearly Rain",
        native_unit_of_measurement="mm",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:weather-rainy",
    ),
)

# Info sensor descriptions (these don't have device classes or state classes)
INFO_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="timezone",
        name="Time Zone",
        icon="mdi:clock-outline",
    ),
    SensorEntityDescription(
        key="dst",
        name="Daylight Saving",
        icon="mdi:weather-sunset",
    ),
    SensorEntityDescription(
        key="device_ip",
        name="Device IP",
        icon="mdi:ip-network",
    ),
    SensorEntityDescription(
        key="wind_unit",
        name="Wind Unit",
        icon="mdi:weather-windy",
    ),
    SensorEntityDescription(
        key="rain_unit",
        name="Rain Unit",
        icon="mdi:weather-rainy",
    ),
    SensorEntityDescription(
        key="pressure_unit",
        name="Pressure Unit",
        icon="mdi:gauge",
    ),
    SensorEntityDescription(
        key="temp_unit",
        name="Temperature Unit",
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key="solar_unit",
        name="Solar Unit",
        icon="mdi:solar-power",
    ),
    SensorEntityDescription(
        key="last_update",
        name="Last Update",
        icon="mdi:clock-check",
    ),
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up WS1500 Legacy platform via YAML."""
    host = config.get(CONF_HOST)
    scan_interval = config.get(CONF_SCAN_INTERVAL, 60)
    resource = f"http://{host}/livedata.htm"

    sensors = []
    # Add weather data sensors
    for description in SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LegacySensor(resource, scan_interval, description))

    # Add info sensors
    for description in INFO_SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LegacyInfoSensor(resource, scan_interval, description))

    async_add_entities(sensors)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up WS1500 Legacy platform via UI."""
    host = config_entry.data[CONF_HOST]
    scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL, 60)
    resource = f"http://{host}/livedata.htm"

    sensors = []
    # Add weather data sensors
    for description in SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LegacySensor(resource, scan_interval, description))

    # Add info sensors
    for description in INFO_SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LegacyInfoSensor(resource, scan_interval, description))

    async_add_entities(sensors)


class WS1500LegacySensor(SensorEntity):
    """Define a WS1500 weather sensor."""

    def __init__(
        self,
        resource: str,
        scan_interval: int,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self._resource = resource
        self._scan_interval = scan_interval
        self.entity_description = description
        self._attr_name = f"WS1500 {description.name}"
        self._attr_unique_id = f"ws1500_legacy_{description.key}"
        self._attr_native_value = None

    def update(self):
        """Update the sensor value."""
        try:
            response = requests.get(self._resource, timeout=10)
            if response.status_code == 200:
                regex_pattern = SENSOR_DATA_MAPPING[self.entity_description.key]
                match = re.search(regex_pattern, response.text)
                if match:
                    raw_value = match.group(1)
                    # Convert to float if possible, otherwise keep as string
                    try:
                        self._attr_native_value = float(raw_value)
                    except ValueError:
                        self._attr_native_value = raw_value
                else:
                    self._attr_native_value = 0
            else:
                self._attr_native_value = None
        except Exception as e:
            _LOGGER.error(f"Error updating WS1500 sensor {self.entity_description.key}: {e}")
            self._attr_native_value = None


class WS1500LegacyInfoSensor(SensorEntity):
    """Define a WS1500 info sensor."""

    def __init__(
        self,
        resource: str,
        scan_interval: int,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self._resource = resource
        self._scan_interval = scan_interval
        self.entity_description = description
        self._attr_name = f"WS1500 {description.name}"
        self._attr_unique_id = f"ws1500_legacy_{description.key}"
        self._attr_native_value = None

    def update(self):
        """Update the sensor value."""
        try:
            host = self._resource.replace("http://", "").replace("/livedata.htm", "")

            if self.entity_description.key == "device_ip":
                self._attr_native_value = host

            elif self.entity_description.key == "last_update":
                self._attr_native_value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            elif self.entity_description.key in [
                "timezone", "dst", "wind_unit", "rain_unit",
                "pressure_unit", "temp_unit", "solar_unit"
            ]:
                # Read device settings from station.htm
                station_url = f"http://{host}/station.htm"
                response = requests.get(station_url, timeout=10)
                if response.status_code == 200:
                    if self.entity_description.key == "timezone":
                        timezone_match = re.search(
                            r'name="timezone"[^>]*value="([-0-9\.]+)"', response.text
                        )
                        if timezone_match:
                            timezone_value = float(timezone_match.group(1))
                            self._attr_native_value = f"UTC{timezone_value:+g}"
                        else:
                            self._attr_native_value = "unknown"

                    elif self.entity_description.key == "dst":
                        dst_match = re.search(
                            r'name="dst".*?<option value="(\d+)"[^>]*selected',
                            response.text,
                            re.DOTALL,
                        )
                        if dst_match:
                            dst_value = int(dst_match.group(1))
                            self._attr_native_value = "on" if dst_value == 1 else "off"
                        else:
                            self._attr_native_value = "unknown"

                    elif self.entity_description.key == "wind_unit":
                        wind_match = re.search(
                            r'name="unit_Wind".*?<option value="(\d+)"[^>]*selected',
                            response.text,
                            re.DOTALL,
                        )
                        if wind_match:
                            unit_value = int(wind_match.group(1))
                            self._attr_native_value = WIND_UNITS.get(unit_value, "unknown")
                        else:
                            self._attr_native_value = "unknown"

                    elif self.entity_description.key == "rain_unit":
                        rain_match = re.search(
                            r'name="u_Rainfall".*?<option value="(\d+)"[^>]*selected',
                            response.text,
                            re.DOTALL,
                        )
                        if rain_match:
                            unit_value = int(rain_match.group(1))
                            self._attr_native_value = RAIN_UNITS.get(unit_value, "unknown")
                        else:
                            self._attr_native_value = "unknown"

                    elif self.entity_description.key == "pressure_unit":
                        pressure_match = re.search(
                            r'name="unit_Pressure".*?<option value="(\d+)"[^>]*selected',
                            response.text,
                            re.DOTALL,
                        )
                        if pressure_match:
                            unit_value = int(pressure_match.group(1))
                            self._attr_native_value = PRESSURE_UNITS.get(unit_value, "unknown")
                        else:
                            self._attr_native_value = "unknown"

                    elif self.entity_description.key == "temp_unit":
                        temp_match = re.search(
                            r'name="u_Temperature".*?<option value="(\d+)"[^>]*selected',
                            response.text,
                            re.DOTALL,
                        )
                        if temp_match:
                            unit_value = int(temp_match.group(1))
                            self._attr_native_value = TEMP_UNITS.get(unit_value, "unknown")
                        else:
                            self._attr_native_value = "unknown"

                    elif self.entity_description.key == "solar_unit":
                        solar_match = re.search(
                            r'name="unit_Solar".*?<option value="(\d+)"[^>]*selected',
                            response.text,
                            re.DOTALL,
                        )
                        if solar_match:
                            unit_value = int(solar_match.group(1))
                            self._attr_native_value = SOLAR_UNITS.get(unit_value, "unknown")
                        else:
                            self._attr_native_value = "unknown"
                else:
                    self._attr_native_value = "unknown"

        except Exception as e:
            _LOGGER.error(f"Error updating WS1500 info sensor {self.entity_description.key}: {e}")
            self._attr_native_value = "unknown"
