# Legacy Ambient Weather WS1500 integration
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers.discovery import async_load_platform

DOMAIN = "ws1500_legacy"

async def async_setup(hass, config):
    """Set up the WS1500 Legacy component."""
    return True

async def async_setup_entry(hass, entry):
    """Set up WS1500 Legacy from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor"])
