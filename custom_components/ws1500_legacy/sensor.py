import logging
import re
import requests
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_RESOURCE, CONF_SCAN_INTERVAL
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVALS = [60, 120, 180, 300, 600]  # 1,2,3,5,10 min
SENSOR_DEFS = [
    # name, unique_id, regex, unit, device_class, state_class, icon
    ("Dirección del Viento", "ws1500_wind_direction", 'name="windir"[^>]*value="([0-9]+)"', "°", "wind_direction", "measurement", "mdi:compass-outline"),
    ("Velocidad del Viento", "ws1500_wind_speed", 'name="avgwind"[^>]*value="([-0-9\\.]+)"', "km/h", "wind_speed", "measurement", "mdi:weather-windy"),
    ("Ráfaga de Viento", "ws1500_wind_gust", 'name="gustspeed"[^>]*value="([-0-9\\.]+)"', "km/h", "wind_speed", "measurement", "mdi:weather-windy-variant"),
    ("Máx. Ráfaga Diaria", "ws1500_max_daily_gust", 'name="dailygust"[^>]*value="([-0-9\\.]+)"', "km/h", "wind_speed", "total_increasing", "mdi:weather-windy-variant"),
    ("Temperatura Exterior", "ws1500_out_temp", 'name="outTemp"[^>]*value="([-0-9\\.]+)"', "°C", "temperature", "measurement", "mdi:thermometer"),
    ("Humedad Exterior", "ws1500_out_humidity", 'name="outHumi"[^>]*value="([0-9]+)"', "%", "humidity", "measurement", "mdi:water-percent"),
    ("Radiación Solar", "ws1500_solar_rad", 'name="solarrad"[^>]*value="([-0-9\\.]+)"', "W/m²", "irradiance", "measurement", "mdi:solar-power"),
    ("Índice UVI", "ws1500_uvi", 'name="uvi"[^>]*value="([0-9]+)"', "UVI", None, "measurement", "mdi:weather-sunny-alert"),
    ("Lluvia por Hora", "ws1500_hourly_rain", 'name="rainofhourly"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation_intensity", "measurement", "mdi:weather-rainy"),
    ("Lluvia Diaria", "ws1500_daily_rain", 'name="rainofdaily"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation", "total_increasing", "mdi:weather-rainy"),
    ("Lluvia Semanal", "ws1500_weekly_rain", 'name="rainofweekly"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation", "total_increasing", "mdi:weather-rainy"),
    ("Lluvia Mensual", "ws1500_monthly_rain", 'name="rainofmonthly"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation", "total_increasing", "mdi:weather-rainy"),
    ("Lluvia Anual", "ws1500_yearly_rain", 'name="rainofyearly"[^>]*value="([-0-9\\.]+)"', "mm", "precipitation", "total_increasing", "mdi:weather-rainy"),
]

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    resource = config.get(CONF_RESOURCE)
    scan_interval = config.get(CONF_SCAN_INTERVAL, 60)
    sensors = [
        WS1500LegacySensor(resource, scan_interval, *sensor_def)
        for sensor_def in SENSOR_DEFS
    ]
    async_add_entities(sensors)

class WS1500LegacySensor(SensorEntity):
    def __init__(self, resource, scan_interval, name, unique_id, regex, unit, device_class, state_class, icon):
        self._resource = resource
        self._scan_interval = scan_interval
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._regex = regex
        self._attr_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        self._state = None

    def update(self):
        try:
            response = requests.get(self._resource, timeout=10)
            if response.status_code == 200:
                value = response.text
                m = re.findall(self._regex, value)
                self._state = m[0] if m else '0'
            else:
                self._state = None
        except Exception as e:
            _LOGGER.error(f"WS1500 sensor error: {e}")
            self._state = None

    @property
    def state(self):
        return self._state
