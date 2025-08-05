import logging
import requests
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "ws1500_legacy"

SERVICE_SET_TIMEZONE = "set_timezone"

SET_TIMEZONE_SCHEMA = vol.Schema({
    vol.Required("host"): cv.string,
    vol.Required("timezone"): vol.All(vol.Coerce(float), vol.Range(min=-12.0, max=12.0)),
    vol.Required("dst"): vol.In([0, 1, "off", "on"]),
})

async def async_setup_services(hass: HomeAssistant):
    """Set up services for WS1500 Legacy."""
    
    async def set_timezone(call: ServiceCall):
        """Service to set the timezone and DST on the WS1500 device."""
        host = call.data.get("host")
        timezone = call.data.get("timezone")
        dst = call.data.get("dst")
        
        # Convert dst to numeric if string
        if dst == "off":
            dst = 0
        elif dst == "on":
            dst = 1
        
        try:
            # Prepare POST data
            station_url = f"http://{host}/station.htm"
            post_data = {
                "timezone": str(timezone),
                "dst": str(dst),
                "Apply": "Apply"
            }
            
            # Perform POST request to change configuration
            response = requests.post(station_url, data=post_data, timeout=10)
            
            if response.status_code == 200:
                dst_text = "on" if dst == 1 else "off"
                _LOGGER.info(f"Successfully set timezone to {timezone} and DST {dst_text} on device {host}")
                hass.bus.async_fire(f"{DOMAIN}_timezone_changed", {
                    "host": host,
                    "timezone": timezone,
                    "dst": dst_text,
                    "success": True
                })
            else:
                _LOGGER.error(f"Failed to set timezone on device {host}. Status: {response.status_code}")
                hass.bus.async_fire(f"{DOMAIN}_timezone_changed", {
                    "host": host,
                    "timezone": timezone,
                    "dst": dst,
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            _LOGGER.error(f"Error setting timezone on device {host}: {e}")
            hass.bus.async_fire(f"{DOMAIN}_timezone_changed", {
                "host": host,
                "timezone": timezone,
                "dst": dst,
                "success": False,
                "error": str(e)
            })

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TIMEZONE,
        set_timezone,
        schema=SET_TIMEZONE_SCHEMA,
    )
