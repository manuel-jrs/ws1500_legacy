"""Config flow for WS1500 Legacy integration."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
    LIVEDATA_ENDPOINT,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


async def validate_host(host: str) -> dict[str, str]:
    """Validate the host can be reached and returns expected data.

    Returns a dict with error key if validation fails, empty dict if success.
    """
    errors: dict[str, str] = {}

    # Basic format validation
    if not host or not host.strip():
        errors["host"] = "invalid_host"
        return errors

    host = host.strip()

    # Try to connect to the device
    url = f"http://{host}{LIVEDATA_ENDPOINT}"

    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        ) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    errors["host"] = "cannot_connect"
                    return errors

                # Verify it's a WS1500 device by checking for expected content
                content = await response.text()
                if 'name="outTemp"' not in content and 'name="windir"' not in content:
                    errors["host"] = "not_ws1500"
                    return errors

    except asyncio.TimeoutError:
        errors["host"] = "timeout"
    except aiohttp.ClientConnectorError:
        errors["host"] = "cannot_connect"
    except aiohttp.ClientError:
        errors["host"] = "cannot_connect"
    except Exception:  # noqa: BLE001
        errors["host"] = "unknown_error"

    return errors


class WS1500LegacyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WS1500 Legacy."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> WS1500LegacyOptionsFlow:
        """Get the options flow for this handler."""
        return WS1500LegacyOptionsFlow(config_entry)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        description_placeholders = {"url_example": "http://<IP>/livedata.htm"}

        if user_input is not None:
            # Validate the host before creating entry
            host = user_input[CONF_HOST].strip()
            user_input[CONF_HOST] = host  # Store cleaned value

            errors = await validate_host(host)

            if not errors:
                # Check if already configured
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"WS1500 ({host})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL),
                    ),
                }
            ),
            errors=errors,
            description_placeholders=description_placeholders,
        )


class WS1500LegacyOptionsFlow(OptionsFlow):
    """Handle options flow for WS1500 Legacy."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate host if it changed
            new_host = user_input[CONF_HOST].strip()
            current_host = self.config_entry.options.get(
                CONF_HOST,
                self.config_entry.data.get(CONF_HOST, ""),
            )

            if new_host != current_host:
                errors = await validate_host(new_host)

            if not errors:
                user_input[CONF_HOST] = new_host  # Store cleaned value
                return self.async_create_entry(title="", data=user_input)

        # Get current values from options first, then fallback to data
        current_host = self.config_entry.options.get(
            CONF_HOST,
            self.config_entry.data.get(CONF_HOST, ""),
        )
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
