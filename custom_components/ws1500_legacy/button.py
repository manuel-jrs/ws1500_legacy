import logging
from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_HOST
from homeassistant.helpers.entity import Entity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up WS1500 Legacy button platform via UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    button = WS1500LegacyRebootButton(coordinator)
    async_add_entities([button])

class WS1500LegacyRebootButton(ButtonEntity):
    def __init__(self, coordinator):
        self._coordinator = coordinator
        self._attr_name = "WS1500 Reboot"
        self._attr_unique_id = "ws1500_legacy_reboot"
        self._attr_icon = "mdi:restart"
        self._attr_device_class = "restart"

    async def async_press(self):
        """Handle the button press to reboot the WS1500."""
        try:
            _LOGGER.info("Attempting to reboot WS1500 weather station...")
            
            success = await self._coordinator.async_reboot_device()
            
            if success:
                # Create a persistent notification
                await self.hass.services.async_call(
                    "persistent_notification",
                    "create",
                    {
                        "title": "WS1500 Weather Station",
                        "message": "Reboot command sent successfully. The weather station should restart in a few moments.",
                        "notification_id": "ws1500_reboot_success"
                    }
                )
            else:
                raise Exception("Reboot command failed")
                
        except Exception as e:
            _LOGGER.error(f"Error sending reboot command to WS1500: {e}")
            # Create error notification
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": "WS1500 Weather Station Error",
                    "message": f"Failed to send reboot command: {str(e)}",
                    "notification_id": "ws1500_reboot_error"
                }
            )
            raise

    @property
    def device_info(self):
        """Return device information."""
        return self._coordinator.get_device_info()
