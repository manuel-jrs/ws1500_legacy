"""Button platform for WS1500 Legacy integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, ENTITY_ID_PREFIX, SENSOR_NAME_PREFIX
from .coordinator import WS1500LegacyCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up WS1500 Legacy button platform via UI."""
    coordinator: WS1500LegacyCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([WS1500LegacyRebootButton(coordinator)])


class WS1500LegacyRebootButton(ButtonEntity):
    """Button to reboot the WS1500 weather station."""

    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator: WS1500LegacyCoordinator) -> None:
        """Initialize the reboot button."""
        self._coordinator = coordinator
        self._attr_name = f"{SENSOR_NAME_PREFIX} Reboot"
        self._attr_unique_id = f"{ENTITY_ID_PREFIX}_reboot"

    async def async_press(self) -> None:
        """Handle the button press to reboot the WS1500."""
        _LOGGER.info("Attempting to reboot WS1500 weather station...")

        success = await self._coordinator.async_reboot_device()

        if success:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "WS1500 Weather Station",
                    "message": (
                        "Reboot command sent successfully. "
                        "The weather station should restart in a few moments."
                    ),
                    "notification_id": "ws1500_reboot_success",
                },
            )
        else:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "WS1500 Weather Station Error",
                    "message": "Failed to send reboot command. Check the logs for details.",
                    "notification_id": "ws1500_reboot_error",
                },
            )
            raise RuntimeError("Reboot command failed")

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return self._coordinator.get_device_info()
