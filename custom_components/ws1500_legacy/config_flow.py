import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import callback

class WS1500LegacyConfigFlow(config_entries.ConfigFlow, domain="ws1500_legacy"):
    VERSION = 1
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="WS1500 Legacy", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_SCAN_INTERVAL, default=60): vol.In([60, 120, 180, 300, 600]),
            }),
            errors=errors,
        )
