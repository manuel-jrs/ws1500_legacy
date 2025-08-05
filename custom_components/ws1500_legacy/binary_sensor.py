import logging
import requests
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up WS1500 Legacy binary sensor platform via YAML."""
    host = config.get(CONF_HOST)
    scan_interval = config.get(CONF_SCAN_INTERVAL, 60)
    resource = f"http://{host}/livedata.htm"
    
    binary_sensor = WS1500LegacyConnectivitySensor(resource, scan_interval)
    async_add_entities([binary_sensor])

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up WS1500 Legacy binary sensor platform via UI."""
    host = config_entry.data[CONF_HOST]
    scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL, 60)
    resource = f"http://{host}/livedata.htm"
    
    binary_sensor = WS1500LegacyConnectivitySensor(resource, scan_interval)
    async_add_entities([binary_sensor])

class WS1500LegacyConnectivitySensor(BinarySensorEntity):
    def __init__(self, resource, scan_interval):
        self._resource = resource
        self._scan_interval = scan_interval
        self._attr_name = "Connectivity"
        self._attr_unique_id = "ws1500_legacy_connectivity"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_icon = "mdi:wifi"
        self._state = None

    def update(self):
        try:
            response = requests.get(self._resource, timeout=10)
            self._state = response.status_code == 200
        except Exception as e:
            _LOGGER.error(f"WS1500 connectivity sensor error: {e}")
            self._state = False

    @property
    def is_on(self):
        return self._state

    @property
    def available(self):
        return True  # Sensor is always available, even if device doesn't respond
