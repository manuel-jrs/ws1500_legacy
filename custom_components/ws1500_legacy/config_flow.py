import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import callback

class WS1500LegacyConfigFlow(config_entries.ConfigFlow, domain="ws1500_legacy"):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        errors = {}
        description_placeholders = {"url_example": "http://<IP>/livedata.htm"}
        if user_input is not None:
            return self.async_create_entry(title="WS1500 Legacy", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_SCAN_INTERVAL, default=60): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
            }),
            errors=errors,
            description_placeholders=description_placeholders
        )
