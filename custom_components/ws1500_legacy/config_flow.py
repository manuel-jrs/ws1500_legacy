"""Config flow for WS1500 Legacy integration."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    LIVEDATA_ENDPOINT,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


async def _validate_host(hass: HomeAssistant, host: str) -> dict[str, str]:
    """Validate the host can be reached and looks like a WS1500.

    Returns a dict with an "host" error key on failure, empty dict on success.
    """
    if not host or not host.strip():
        return {"host": "invalid_host"}

    url = f"http://{host.strip()}{LIVEDATA_ENDPOINT}"
    session = async_get_clientsession(hass)

    try:
        async with asyncio.timeout(DEFAULT_TIMEOUT):
            async with session.get(url) as response:
                if response.status != 200:
                    return {"host": "cannot_connect"}
                content = await response.text()
    except asyncio.TimeoutError:
        return {"host": "timeout"}
    except aiohttp.ClientConnectorError:
        return {"host": "cannot_connect"}
    except aiohttp.ClientError:
        return {"host": "cannot_connect"}

    if 'name="outTemp"' not in content and 'name="windir"' not in content:
        return {"host": "not_ws1500"}

    return {}


_DATA_SCHEMA_FIELDS = {
    vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
        vol.Coerce(int),
        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
    ),
}


class WS1500LegacyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WS1500 Legacy."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> WS1500LegacyOptionsFlow:
        """Get the options flow for this handler."""
        return WS1500LegacyOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            user_input[CONF_HOST] = host

            errors = await _validate_host(self.hass, host)

            if not errors:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"WS1500 ({host})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_HOST): str, **_DATA_SCHEMA_FIELDS}
            ),
            errors=errors,
            description_placeholders={"url_example": "http://<IP>/livedata.htm"},
        )


class WS1500LegacyOptionsFlow(OptionsFlow):
    """Handle options flow for WS1500 Legacy.

    HA 2024.12+ auto-assigns ``self.config_entry``. Do not declare ``__init__``
    or set it manually — that pattern was removed in HA 2025.12.
    """

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        current_host = self.config_entry.options.get(
            CONF_HOST,
            self.config_entry.data.get(CONF_HOST, ""),
        )

        if user_input is not None:
            new_host = user_input[CONF_HOST].strip()
            if new_host != current_host:
                errors = await _validate_host(self.hass, new_host)

            if not errors:
                user_input[CONF_HOST] = new_host
                return self.async_create_entry(title="", data=user_input)

        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=current_host): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=current_scan_interval
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
            errors=errors,
        )
