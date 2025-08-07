# Legacy Ambient Weather WS1500 integration
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers.discovery import async_load_platform

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .coordinator import WS1500LegacyCoordinator

async def async_setup(hass, config):
    """Set up the WS1500 Legacy component."""
    return True

async def async_setup_entry(hass, entry):
    """Set up WS1500 Legacy from a config entry."""
    # Store the config entry for future reference
    hass.data.setdefault(DOMAIN, {})
    
    # Get configuration
    host = entry.data[CONF_HOST]
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL, 
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    
    # Create coordinator
    coordinator = WS1500LegacyCoordinator(hass, host, scan_interval)
    
    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Set up update listener for options changes
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor", "button"])
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor", "button"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_update_options(hass, entry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
