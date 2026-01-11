"""Support for WS1500 Legacy Weather Station sensors."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

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

# Smart calculated sensors
SMART_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="last_rain_date",
        name="Last Rain Date",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:weather-rainy-clock",
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

    # Add smart calculated sensors
    for description in SMART_SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LastRainSensor(coordinator, description))

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

    # Add smart calculated sensors
    for description in SMART_SENSOR_DESCRIPTIONS:
        sensors.append(WS1500LastRainSensor(coordinator, description))

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


class WS1500LastRainSensor(CoordinatorEntity[WS1500LegacyCoordinator], RestoreSensor):
    """Smart sensor that tracks when it last rained based on daily rain changes."""

    _last_rain_date: datetime | None = None

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

    async def async_added_to_hass(self) -> None:
        """Restore last known state."""
        await super().async_added_to_hass()

        # Restore the last known rain date
        restored_data = await self.async_get_last_sensor_data()
        if restored_data and restored_data.native_value:
            restored_value = restored_data.native_value
            # Handle both datetime objects and ISO format strings
            if isinstance(restored_value, datetime):
                self._last_rain_date = dt_util.as_local(restored_value)
            elif isinstance(restored_value, str):
                parsed = dt_util.parse_datetime(restored_value)
                if parsed:
                    self._last_rain_date = dt_util.as_local(parsed)
            _LOGGER.info("Restored last rain date: %s", self._last_rain_date)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # Check for rain today and update last rain date
        current_daily_rain = self.coordinator.data["sensors"].get("daily_rain")

        if current_daily_rain is not None and current_daily_rain > 0:
            # It's raining today, update the last rain date to today
            today = dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if self._last_rain_date is None or self._last_rain_date.date() != today.date():
                self._last_rain_date = today
                _LOGGER.info("Rain detected today! Updated last rain date to: %s", today)

        # Call parent to trigger state update
        super()._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True  # Always available, even if no rain detected yet

    @property
    def native_value(self) -> datetime | None:
        """Return the last rain date."""
        return self._last_rain_date

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        daily_rain = self.coordinator.data["sensors"].get("daily_rain", 0)

        attrs: dict[str, Any] = {
            "daily_rain_mm": daily_rain,
            "detection_method": "daily_rain_sensor",
        }

        if self._last_rain_date:
            now = dt_util.now()
            days_since = (now.date() - self._last_rain_date.date()).days
            attrs["days_since_rain"] = days_since

            if days_since == 0:
                attrs["rain_status"] = "raining_today"
            elif days_since == 1:
                attrs["rain_status"] = "rained_yesterday"
            elif days_since <= 7:
                attrs["rain_status"] = "recent_rain"
            else:
                attrs["rain_status"] = "no_recent_rain"
        else:
            attrs["rain_status"] = "no_rain_detected"
            attrs["days_since_rain"] = None

        return attrs

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info()
