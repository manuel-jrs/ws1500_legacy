"""Binary sensor platform for WS1500 Legacy integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
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


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up WS1500 Legacy binary sensor platform via YAML."""
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

    async_add_entities([
        WS1500LegacyConnectivitySensor(coordinator),
        WS1500IsRainingSensor(coordinator),
    ])


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WS1500 Legacy binary sensor platform via UI."""
    coordinator: WS1500LegacyCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([
        WS1500LegacyConnectivitySensor(coordinator),
        WS1500IsRainingSensor(coordinator),
    ])


class WS1500LegacyConnectivitySensor(
    CoordinatorEntity[WS1500LegacyCoordinator],
    BinarySensorEntity,
):
    """Binary sensor representing device connectivity."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:wifi"

    def __init__(self, coordinator: WS1500LegacyCoordinator) -> None:
        """Initialize the connectivity sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{SENSOR_NAME_PREFIX} Connectivity"
        self._attr_unique_id = f"{ENTITY_ID_PREFIX}_connectivity"

    @property
    def is_on(self) -> bool:
        """Return True if the device is connected."""
        return self.coordinator.last_update_success

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True  # Sensor is always available to report connection status

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info()


class WS1500IsRainingSensor(
    CoordinatorEntity[WS1500LegacyCoordinator],
    BinarySensorEntity,
):
    """Binary sensor indicating if it's currently raining."""

    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, coordinator: WS1500LegacyCoordinator) -> None:
        """Initialize the rain sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{SENSOR_NAME_PREFIX} Is Raining"
        self._attr_unique_id = f"{ENTITY_ID_PREFIX}_is_raining"

    @property
    def is_on(self) -> bool | None:
        """Return True if it's currently raining (hourly_rain > 0)."""
        hourly_rain = self.coordinator.data["sensors"].get("hourly_rain")
        if hourly_rain is None:
            return None
        return hourly_rain > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        sensors = self.coordinator.data.get("sensors", {})
        return {
            "hourly_rain_mm": sensors.get("hourly_rain"),
            "daily_rain_mm": sensors.get("daily_rain"),
            "event_rain_mm": sensors.get("event_rain"),
        }

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info()
