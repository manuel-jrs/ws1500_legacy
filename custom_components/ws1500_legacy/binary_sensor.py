"""Binary sensor platform for WS1500 Legacy integration."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import WS1500ConfigEntry
from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    ENTITY_ID_PREFIX,
    SENSOR_NAME_PREFIX,
)
from .coordinator import WS1500LegacyCoordinator


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the binary sensor platform via YAML (legacy path)."""
    host: str = config[CONF_HOST]
    scan_interval: int = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    hass.data.setdefault(DOMAIN, {})
    yaml_key = f"yaml_{host}"
    lock_key = f"yaml_lock_{host}"

    if lock_key not in hass.data[DOMAIN]:
        hass.data[DOMAIN][lock_key] = asyncio.Lock()

    async with hass.data[DOMAIN][lock_key]:
        if yaml_key not in hass.data[DOMAIN]:
            coordinator = WS1500LegacyCoordinator(hass, host, scan_interval)
            await coordinator.async_config_entry_first_refresh()
            hass.data[DOMAIN][yaml_key] = coordinator
        else:
            coordinator = hass.data[DOMAIN][yaml_key]

    async_add_entities([WS1500LegacyConnectivitySensor(coordinator)])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WS1500ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform via UI."""
    async_add_entities([WS1500LegacyConnectivitySensor(entry.runtime_data)])


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
        """Return True if the last update succeeded."""
        return self.coordinator.last_update_success

    @property
    def available(self) -> bool:
        """The connectivity sensor is the source of truth — always available."""
        return True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info()
