"""Support for WS1500 Legacy Weather Station sensors."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    PERCENTAGE,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfPressure,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENTITY_ID_PREFIX,
    SENSOR_NAME_PREFIX,
)
from .coordinator import WS1500LegacyCoordinator

_LOGGER = logging.getLogger(__name__)

# Weather sensor descriptions following Home Assistant standards
SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="wind_direction",
        name="Wind Direction",
        native_unit_of_measurement="°",
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
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
        state_class=SensorStateClass.MEASUREMENT,
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
        key="in_temp",
        name="Indoor Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key="in_humidity",
        name="Indoor Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-percent",
    ),
    SensorEntityDescription(
        key="abs_pressure",
        name="Absolute Pressure",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
    ),
    SensorEntityDescription(
        key="rel_pressure",
        name="Relative Pressure",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
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
        native_unit_of_measurement="mm/h",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-rainy",
    ),
    SensorEntityDescription(
        key="event_rain",
        name="Event Rain",
        native_unit_of_measurement="mm",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
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
    SensorEntityDescription(
        key="pm25_indoor",
        name="PM2.5 Indoor",
        native_unit_of_measurement="µg/m³",
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:air-filter",
    ),
    SensorEntityDescription(
        key="pm25_outdoor",
        name="PM2.5 Outdoor",
        native_unit_of_measurement="µg/m³",
        device_class=SensorDeviceClass.PM25,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:air-filter",
    ),
)

# Info sensor descriptions (these don't have device classes or state classes)
INFO_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="timezone",
        name="Time Zone",
        icon="mdi:clock-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="dst",
        name="Daylight Saving",
        icon="mdi:weather-sunset",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="device_ip",
        name="Device IP",
        icon="mdi:ip-network",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="wind_unit",
        name="Wind Unit",
        icon="mdi:weather-windy",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="rain_unit",
        name="Rain Unit",
        icon="mdi:weather-rainy",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="pressure_unit",
        name="Pressure Unit",
        icon="mdi:gauge",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="temp_unit",
        name="Temperature Unit",
        icon="mdi:thermometer",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="solar_unit",
        name="Solar Unit",
        icon="mdi:solar-power",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="last_update",
        name="Last Update",
        icon="mdi:clock-check",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="outdoor1_id",
        name="Outdoor Sensor ID",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="outdoor1_battery",
        name="Outdoor Sensor Battery",
        icon="mdi:battery",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="current_time",
        name="Receiver Time",
        icon="mdi:clock",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up WS1500 Legacy platform via YAML."""
    host: str = config[CONF_HOST]
    scan_interval: int = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Use shared coordinator for YAML setup to avoid duplicates
    hass.data.setdefault(DOMAIN, {})
    yaml_key = f"yaml_{host}"
    lock_key = f"yaml_lock_{host}"

    # Create a lock for this host if it doesn't exist
    if lock_key not in hass.data[DOMAIN]:
        hass.data[DOMAIN][lock_key] = asyncio.Lock()

    # Use the lock to prevent race conditions when multiple platforms initialize
    async with hass.data[DOMAIN][lock_key]:
        if yaml_key not in hass.data[DOMAIN]:
            # Create coordinator only if not already created by another platform
            coordinator = WS1500LegacyCoordinator(hass, host, scan_interval)
            await coordinator.async_config_entry_first_refresh()
            hass.data[DOMAIN][yaml_key] = coordinator
        else:
            coordinator = hass.data[DOMAIN][yaml_key]

    sensors: list[SensorEntity] = []

    # Add weather data sensors
    for description in SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LegacySensor(coordinator, description))

    # Add info sensors
    for description in INFO_SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LegacyInfoSensor(coordinator, description))

    async_add_entities(sensors)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WS1500 Legacy platform via UI."""
    coordinator: WS1500LegacyCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors: list[SensorEntity] = []

    # Add weather data sensors
    for description in SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LegacySensor(coordinator, description))

    # Add info sensors
    for description in INFO_SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LegacyInfoSensor(coordinator, description))

    async_add_entities(sensors)


class WS1500LegacySensor(CoordinatorEntity[WS1500LegacyCoordinator], SensorEntity):
    """Define a WS1500 weather sensor."""

    def __init__(
        self,
        coordinator: WS1500LegacyCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{SENSOR_NAME_PREFIX} {description.name}"
        self._attr_unique_id = f"{ENTITY_ID_PREFIX}_{description.key}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.native_value is not None

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        return self.coordinator.data["sensors"].get(self.entity_description.key)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info()


class WS1500LegacyInfoSensor(CoordinatorEntity[WS1500LegacyCoordinator], SensorEntity):
    """Define a WS1500 info sensor."""

    def __init__(
        self,
        coordinator: WS1500LegacyCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{SENSOR_NAME_PREFIX} {description.name}"
        self._attr_unique_id = f"{ENTITY_ID_PREFIX}_{description.key}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.native_value is not None

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        # Check if this sensor is in the sensors data (including info sensors from livedata)
        value = self.coordinator.data["sensors"].get(self.entity_description.key)
        if value is not None:
            return value
        # If not found in sensors, check in info data
        return self.coordinator.data["info"].get(self.entity_description.key)

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info()
