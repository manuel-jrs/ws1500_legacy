"""Utility functions for WS1500 Legacy integration."""

import logging
from typing import Any, Dict

from .const import (
    DOMAIN,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_SW_VERSION,
    DEVICE_SUGGESTED_AREA,
)

_LOGGER = logging.getLogger(__name__)


def get_device_info(host: str) -> Dict[str, Any]:
    """Return standardized device information for all entities."""
    return {
        "identifiers": {(DOMAIN, host)},
        "name": f"WS1500 Weather Station ({host})",
        "manufacturer": DEVICE_MANUFACTURER,
        "model": DEVICE_MODEL,
        "sw_version": DEVICE_SW_VERSION,
        "configuration_url": f"http://{host}",
        "suggested_area": DEVICE_SUGGESTED_AREA,
    }


def parse_numeric_value(raw_value: str) -> float:
    """Parse a string value to float, with error handling."""
    try:
        return float(raw_value)
    except (ValueError, TypeError):
        _LOGGER.warning(f"Could not parse numeric value: {raw_value}")
        return 0.0


def format_timezone(timezone_value: float) -> str:
    """Format timezone offset for display."""
    return f"UTC{timezone_value:+g}"


def format_dst_status(dst_value: int) -> str:
    """Format DST status for display."""
    return "on" if dst_value == 1 else "off"


def safe_get_unit(unit_dict: Dict[int, str], unit_value: int, default: str = "unknown") -> str:
    """Safely get unit string from unit dictionary."""
    return unit_dict.get(unit_value, default)
