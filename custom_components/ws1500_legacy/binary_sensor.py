import logging
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.const import CONF_HOST, CONF_SCAN_INTERVAL
from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL
from .coordinator import WS1500LegacyCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up WS1500 Legacy binary sensor platform via YAML."""
    host = config.get(CONF_HOST)
    scan_interval = config.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    
    # Create coordinator for YAML setup
    coordinator = WS1500LegacyCoordinator(hass, host, scan_interval)
    await coordinator.async_config_entry_first_refresh()
    
    binary_sensor = WS1500LegacyConnectivitySensor(coordinator)
    async_add_entities([binary_sensor])

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up WS1500 Legacy binary sensor platform via UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    binary_sensor = WS1500LegacyConnectivitySensor(coordinator)
    async_add_entities([binary_sensor])

class WS1500LegacyConnectivitySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator: WS1500LegacyCoordinator):
        super().__init__(coordinator)
        self._attr_name = "WS1500 Connectivity"
        self._attr_unique_id = "ws1500_legacy_connectivity"
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_icon = "mdi:wifi"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def is_on(self):
        """Return True if the device is connected."""
        # The coordinator handles connectivity by successfully fetching data
        return self.coordinator.last_update_success

    @property
    def available(self):
        """Return True if entity is available."""
        return True  # Sensor is always available, even if device doesn't respond

    @property
    def device_info(self):
        """Return device information."""
        return self.coordinator.get_device_info()
