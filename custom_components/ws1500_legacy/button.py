"""Button platform for WS1500 Legacy integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import WS1500ConfigEntry
from .const import ENTITY_ID_PREFIX, SENSOR_NAME_PREFIX
from .coordinator import WS1500LegacyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WS1500ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform via UI."""
    async_add_entities([WS1500LegacyRebootButton(entry.runtime_data)])


class WS1500LegacyRebootButton(
    CoordinatorEntity[WS1500LegacyCoordinator],
    ButtonEntity,
):
    """Button to reboot the WS1500 weather station."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator: WS1500LegacyCoordinator) -> None:
        """Initialize the reboot button."""
        super().__init__(coordinator)
        self._attr_name = f"{SENSOR_NAME_PREFIX} Reboot"
        self._attr_unique_id = f"{ENTITY_ID_PREFIX}_reboot"

    async def async_press(self) -> None:
        """Send the reboot command to the device."""
        _LOGGER.info("Sending reboot command to WS1500 weather station")

        if not await self.coordinator.async_reboot_device():
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "WS1500 Weather Station Error",
                    "message": (
                        "Failed to send reboot command. Check the logs for details."
                    ),
                    "notification_id": "ws1500_reboot_error",
                },
            )
            raise RuntimeError("Reboot command failed")

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self.coordinator.get_device_info()
