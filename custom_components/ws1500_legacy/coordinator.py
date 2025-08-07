"""Coordinator for WS1500 Legacy integration."""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CACHE_DURATION,
    DATA_CACHE_DURATION,
    DEFAULT_TIMEOUT,
    DOMAIN,
    LIVEDATA_ENDPOINT,
    PRESSURE_UNIT_PATTERN,
    PRESSURE_UNITS,
    RAIN_UNIT_PATTERN,
    RAIN_UNITS,
    SENSOR_DATA_MAPPING,
    SOLAR_UNIT_PATTERN,
    SOLAR_UNITS,
    STATION_ENDPOINT,
    TEMP_UNIT_PATTERN,
    TEMP_UNITS,
    TIMEZONE_PATTERN,
    DST_PATTERN,
    WIND_UNIT_PATTERN,
    WIND_UNITS,
)

_LOGGER = logging.getLogger(__name__)


class WS1500LegacyCoordinator(DataUpdateCoordinator):
    """Class to manage fetching WS1500 data from the API."""

    def __init__(self, hass: HomeAssistant, host: str, scan_interval: int) -> None:
        """Initialize the coordinator."""
        self.host = host
        self.livedata_url = f"http://{host}{LIVEDATA_ENDPOINT}"
        self.station_url = f"http://{host}{STATION_ENDPOINT}"
        
        # Cache for station settings (changes infrequently)
        self._station_cache: Dict[str, Any] = {}
        self._station_cache_time: Optional[datetime] = None
        
        # Compiled regex patterns for better performance
        self._compiled_patterns = {
            key: re.compile(pattern) 
            for key, pattern in SENSOR_DATA_MAPPING.items()
        }
        self._station_patterns = {
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

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from API endpoint."""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
        ) as session:
            try:
                # Fetch live data (weather sensors)
                sensor_data = await self._fetch_sensor_data(session)
                
                # Fetch station settings (cached for performance)
                station_data = await self._fetch_station_data(session)
                
                # Add derived data
                info_data = {
                    "device_ip": self.host,
                    "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    **station_data,
                }
                
                return {
                    "sensors": sensor_data,
                    "info": info_data,
                }
                
            except Exception as err:
                raise UpdateFailed(f"Error communicating with API: {err}")

    async def _fetch_sensor_data(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Fetch sensor data from livedata.htm."""
        try:
            async with session.get(self.livedata_url) as response:
                response.raise_for_status()
                content = await response.text()
                
                sensor_data = {}
                for key, pattern in self._compiled_patterns.items():
                    match = pattern.search(content)
                    if match:
                        raw_value = match.group(1)
                        try:
                            sensor_data[key] = float(raw_value)
                        except ValueError:
                            sensor_data[key] = raw_value
                    else:
                        sensor_data[key] = 0
                
                return sensor_data
                
        except Exception as err:
            _LOGGER.error(f"Error fetching sensor data: {err}")
            raise

    async def _fetch_station_data(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Fetch station settings with caching."""
        now = datetime.now()
        
        # Return cached data if still valid
        if (self._station_cache_time and 
            now - self._station_cache_time < timedelta(seconds=CACHE_DURATION)):
            return self._station_cache
        
        try:
            async with session.get(self.station_url) as response:
                response.raise_for_status()
                content = await response.text()
                
                station_data = {}
                
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
                unit_mappings = [
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
                
        except Exception as err:
            _LOGGER.error(f"Error fetching station data: {err}")
            # Return cached data if available, otherwise defaults
            if self._station_cache:
                return self._station_cache
            return {
                "timezone": "unknown",
                "dst": "unknown",
                "wind_unit": "unknown",
                "rain_unit": "unknown",
                "pressure_unit": "unknown",
                "temp_unit": "unknown",
                "solar_unit": "unknown",
            }

    async def async_reboot_device(self) -> bool:
        """Send reboot command to the device."""
        reboot_url = f"http://{self.host}/msgreboot.htm"
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT)
            ) as session:
                async with session.get(reboot_url) as response:
                    response.raise_for_status()
                    _LOGGER.info("WS1500 reboot command sent successfully")
                    return True
                    
        except Exception as err:
            _LOGGER.error(f"Error sending reboot command: {err}")
            return False

    def get_device_info(self) -> Dict[str, Any]:
        """Return standardized device information."""
        from .const import (
            DEVICE_MANUFACTURER,
            DEVICE_MODEL,
            DEVICE_SW_VERSION,
            DEVICE_SUGGESTED_AREA,
        )
        
        return {
            "identifiers": {(DOMAIN, self.host)},
            "name": f"WS1500 Weather Station ({self.host})",
            "manufacturer": DEVICE_MANUFACTURER,
            "model": DEVICE_MODEL,
            "sw_version": DEVICE_SW_VERSION,
            "configuration_url": f"http://{self.host}",
            "suggested_area": DEVICE_SUGGESTED_AREA,
        }
