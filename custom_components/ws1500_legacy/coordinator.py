"""Coordinator for WS1500 Legacy integration."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CACHE_DURATION,
    DEFAULT_STATION_DATA,
    DEFAULT_TIMEOUT,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME_TEMPLATE,
    DEVICE_SUGGESTED_AREA,
    DEVICE_SW_VERSION,
    DOMAIN,
    DST_PATTERN,
    INFO_SENSOR_MAPPING,
    LIVEDATA_ENDPOINT,
    PRESSURE_SENSORS,
    PRESSURE_UNIT_PATTERN,
    PRESSURE_UNITS,
    RAIN_SENSORS,
    RAIN_UNIT_PATTERN,
    RAIN_UNITS,
    REBOOT_ENDPOINT,
    SENSOR_DATA_MAPPING,
    SOLAR_SENSORS,
    SOLAR_UNIT_PATTERN,
    SOLAR_UNITS,
    STATION_ENDPOINT,
    TEMP_UNIT_PATTERN,
    TEMP_UNITS,
    TEMPERATURE_SENSORS,
    TIMEZONE_PATTERN,
    UNAVAILABLE_VALUES,
    WIND_SENSORS,
    WIND_UNIT_PATTERN,
    WIND_UNITS,
    convert_pressure,
    convert_rain,
    convert_solar,
    convert_temperature,
    convert_wind_speed,
)

_LOGGER = logging.getLogger(__name__)


class WS1500LegacyCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching WS1500 data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.host = host
        self.livedata_url = f"http://{host}{LIVEDATA_ENDPOINT}"
        self.station_url = f"http://{host}{STATION_ENDPOINT}"
        self.reboot_url = f"http://{host}{REBOOT_ENDPOINT}"

        # Use Home Assistant's shared aiohttp session (persistent, efficient)
        self._session: aiohttp.ClientSession = async_get_clientsession(hass)

        # Cache for station settings (changes infrequently)
        self._station_cache: dict[str, Any] = {}
        self._station_cache_time: datetime | None = None

        # Compiled regex patterns for better performance
        self._compiled_patterns: dict[str, re.Pattern[str]] = {
            key: re.compile(pattern)
            for key, pattern in SENSOR_DATA_MAPPING.items()
        }
        self._info_patterns: dict[str, re.Pattern[str]] = {
            key: re.compile(pattern)
            for key, pattern in INFO_SENSOR_MAPPING.items()
        }
        self._station_patterns: dict[str, re.Pattern[str]] = {
            "timezone": re.compile(TIMEZONE_PATTERN),
            "dst": re.compile(DST_PATTERN, re.DOTALL),
            "wind_unit": re.compile(WIND_UNIT_PATTERN, re.DOTALL),
            "rain_unit": re.compile(RAIN_UNIT_PATTERN, re.DOTALL),
            "pressure_unit": re.compile(PRESSURE_UNIT_PATTERN, re.DOTALL),
            "temp_unit": re.compile(TEMP_UNIT_PATTERN, re.DOTALL),
            "solar_unit": re.compile(SOLAR_UNIT_PATTERN, re.DOTALL),
        }

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        try:
            # Fetch station settings first (cached, needed for unit conversion)
            station_data = await self._fetch_station_data()

            # Fetch live data (weather sensors)
            raw_sensor_data = await self._fetch_sensor_data()

            # Convert sensor data to metric units based on device configuration
            sensor_data = self._convert_units(raw_sensor_data, station_data)

            # Build info data
            info_data = {
                "device_ip": self.host,
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                **station_data,
            }

            return {
                "sensors": sensor_data,
                "info": info_data,
            }

        except asyncio.TimeoutError as err:
            raise UpdateFailed(f"Timeout connecting to {self.host}") from err
        except aiohttp.ClientConnectorError as err:
            raise UpdateFailed(
                f"Cannot connect to {self.host}: device may be offline"
            ) from err
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(
                f"HTTP error from {self.host}: {err.status}"
            ) from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(
                f"Connection error to {self.host}: {err}"
            ) from err

    def _convert_units(
        self,
        sensor_data: dict[str, Any],
        station_data: dict[str, str],
    ) -> dict[str, Any]:
        """Convert sensor values to metric units based on device configuration."""
        converted = sensor_data.copy()

        temp_unit = station_data.get("temp_unit", "°C")
        wind_unit = station_data.get("wind_unit", "km/h")
        rain_unit = station_data.get("rain_unit", "mm")
        pressure_unit = station_data.get("pressure_unit", "hPa")
        solar_unit = station_data.get("solar_unit", "W/m²")

        for key, value in sensor_data.items():
            if value is None:
                continue

            if key in TEMPERATURE_SENSORS:
                converted[key] = convert_temperature(value, temp_unit)
            elif key in WIND_SENSORS:
                converted[key] = convert_wind_speed(value, wind_unit)
            elif key in RAIN_SENSORS:
                converted[key] = convert_rain(value, rain_unit)
            elif key in PRESSURE_SENSORS:
                converted[key] = convert_pressure(value, pressure_unit)
            elif key in SOLAR_SENSORS:
                converted[key] = convert_solar(value, solar_unit)

        return converted

    async def _fetch_sensor_data(self) -> dict[str, Any]:
        """Fetch sensor data from livedata.htm."""
        async with asyncio.timeout(DEFAULT_TIMEOUT):
            async with self._session.get(self.livedata_url) as response:
                response.raise_for_status()
                content = await response.text()

        sensor_data: dict[str, Any] = {}

        for key, pattern in self._compiled_patterns.items():
            match = pattern.search(content)
            if match:
                raw_value = match.group(1)
                try:
                    if raw_value in UNAVAILABLE_VALUES:
                        sensor_data[key] = None
                    else:
                        sensor_data[key] = float(raw_value)
                except ValueError:
                    sensor_data[key] = raw_value
            else:
                sensor_data[key] = None

        # Also extract info sensors from livedata
        for key, pattern in self._info_patterns.items():
            match = pattern.search(content)
            if match:
                value = match.group(1)
                if value in UNAVAILABLE_VALUES:
                    sensor_data[key] = None
                else:
                    sensor_data[key] = value
            else:
                sensor_data[key] = None

        return sensor_data

    async def _fetch_station_data(self) -> dict[str, Any]:
        """Fetch station settings with caching."""
        now = datetime.now()

        # Return cached data if still valid
        if (
            self._station_cache_time
            and now - self._station_cache_time < timedelta(seconds=CACHE_DURATION)
        ):
            return self._station_cache

        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                async with self._session.get(self.station_url) as response:
                    response.raise_for_status()
                    content = await response.text()

            station_data: dict[str, Any] = {}

            # Parse timezone
            match = self._station_patterns["timezone"].search(content)
            if match:
                timezone_value = float(match.group(1))
                station_data["timezone"] = f"UTC{timezone_value:+g}"
            else:
                station_data["timezone"] = "unknown"

            # Parse DST
            match = self._station_patterns["dst"].search(content)
            if match:
                dst_value = int(match.group(1))
                station_data["dst"] = "on" if dst_value == 1 else "off"
            else:
                station_data["dst"] = "unknown"

            # Parse units
            unit_mappings: list[tuple[str, dict[int, str]]] = [
                ("wind_unit", WIND_UNITS),
                ("rain_unit", RAIN_UNITS),
                ("pressure_unit", PRESSURE_UNITS),
                ("temp_unit", TEMP_UNITS),
                ("solar_unit", SOLAR_UNITS),
            ]

            for key, unit_dict in unit_mappings:
                match = self._station_patterns[key].search(content)
                if match:
                    unit_value = int(match.group(1))
                    station_data[key] = unit_dict.get(unit_value, "unknown")
                else:
                    station_data[key] = "unknown"

            # Cache the results
            self._station_cache = station_data
            self._station_cache_time = now

            return station_data

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning(
                "Error fetching station settings: %s (using cached/default values)",
                err,
            )
            return self._station_cache if self._station_cache else DEFAULT_STATION_DATA.copy()

    async def async_reboot_device(self) -> bool:
        """Send reboot command to the device."""
        try:
            async with asyncio.timeout(DEFAULT_TIMEOUT):
                async with self._session.get(self.reboot_url) as response:
                    response.raise_for_status()
                    _LOGGER.info(
                        "WS1500 reboot command sent successfully to %s",
                        self.host,
                    )
                    return True

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout sending reboot command to %s", self.host)
            return False
        except aiohttp.ClientError as err:
            _LOGGER.error(
                "Error sending reboot command to %s: %s",
                self.host,
                err,
            )
            return False

    def get_device_info(self) -> dict[str, Any]:
        """Return standardized device information."""
        return {
            "identifiers": {(DOMAIN, self.host)},
            "name": DEVICE_NAME_TEMPLATE.format(host=self.host),
            "manufacturer": DEVICE_MANUFACTURER,
            "model": DEVICE_MODEL,
            "sw_version": DEVICE_SW_VERSION,
            "configuration_url": f"http://{self.host}",
            "suggested_area": DEVICE_SUGGESTED_AREA,
        }
