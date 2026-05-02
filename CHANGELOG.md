# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] - 2026-05-01

### Bug fixes

- **Footcandle solar conversion was ~116× too small.** The `fc → W/m²` factor in `convert_solar` used the inverse direction (lux→fc) of the lux conversion. Corrected to `v * 10.764 * 0.0079`. Only affected users with the device's solar unit set to footcandles.
- **`uvi` and `wind_direction` regex rejected decimal values.** Modern WS1500 firmwares can report fractional UVI (e.g. `3.2`); the patterns now accept decimals.
- **Sensors stayed "available" with stale values after coordinator failure.** `WS1500LegacySensor` and `WS1500LegacyInfoSensor` now combine `CoordinatorEntity.available` (which checks `last_update_success`) with the per-key None check.
- **Frozen-receiver detection.** When the WS1500 returns HTTP 200 with identical HTML for minutes (the receiver hangs but the web server keeps serving the last snapshot), the coordinator now raises `UpdateFailed` so entities go unavailable instead of reporting a flat-line value. Detected by tracking the device's `CurrTime` field — when it has not advanced for ≥180s of wall-clock time, the receiver is considered frozen. Threshold configurable via `STALE_CURRTIME_THRESHOLD_SECONDS` in `const.py`.

### Home Assistant compatibility (2024.12+ / 2025.12+)

- Migrated to `ConfigEntry.runtime_data` and a typed `WS1500ConfigEntry`. `hass.data[DOMAIN][entry.entry_id]` is no longer used for the config-flow path.
- `OptionsFlow` no longer declares `__init__`; relies on the framework-assigned `self.config_entry`. The legacy pattern was removed in HA 2025.12.
- `FlowResult` import replaced by `ConfigFlowResult` from `homeassistant.config_entries`.
- Config flow validation now reuses the shared `aiohttp` session via `async_get_clientsession`.
- Added `SensorDeviceClass.UV_INDEX` to the UVI sensor.
- `manifest.json` modernized: added `integration_type: device`, `loggers`, `issue_tracker`, `quality_scale: bronze`.
- Reboot button now extends `CoordinatorEntity` for proper coordinator lifecycle binding; success notification removed (only errors notify).

### Cleanup

- Deleted unused `utils.py` (all functions either reimplemented in `coordinator.py` or unreferenced).
- Removed dead constants `INTEGRATION_NAME` and `DATA_CACHE_DURATION`.
- Standardized `inHumi` regex to match `outHumi`.

### Notes for users

- Entity `unique_id`s are unchanged — your dashboards, automations, and statistics history are preserved.
- The YAML setup path is preserved for backwards compatibility but is not recommended for new installs.

## [0.6.0] - 2025-08-09

### ✅ **Configuration Fixes and Device Validation**

**Based on actual WS1500 device testing at 192.168.1.198:**

#### **Fixed Configurations:**
- **Wind Direction**: Fixed to always use `SensorStateClass.MEASUREMENT_ANGLE` as requested
  - Uses backward compatibility for older Home Assistant versions  
  - Proper compass/angular measurement state class
- **Device Validation**: Tested against real device to ensure all sensor mappings are correct

#### **Removed Non-Existent Features:**
- **Removed Last Rain Sensor**: After checking the actual device, confirmed that `lastrain` field does not exist
  - WS1500 devices don't provide timestamp for last rain event
  - Removed implementation to avoid false sensor readings
  - All rain accumulation sensors (hourly, daily, weekly, monthly, yearly) remain available

#### **Validated Sensor List:**
Based on real device testing, confirmed these sensors are available:
- ✅ **Wind**: direction, speed, gust, max daily gust
- ✅ **Temperature**: outdoor (indoor showing `--.-` - not connected)
- ✅ **Humidity**: outdoor (indoor showing `--` - not connected) 
- ✅ **Rain**: hourly rate, event, daily, weekly, monthly, yearly totals
- ✅ **Solar**: radiation and UV index
- ✅ **Pressure**: absolute and relative (showing `----` - may not be connected)
- ✅ **Air Quality**: PM2.5 indoor/outdoor (may not be connected)

#### **Technical Details:**
- All sensor configurations now pass Home Assistant validation (20 valid sensors, 0 errors)
- Uses device's native field names confirmed from live device
- Proper handling of unavailable sensors (shows `unknown` when not connected)

### Benefits
- **Accurate Configuration**: Only includes sensors actually available on WS1500 devices
- **Standards Compliant**: Wind direction uses proper angular measurement state class
- **Reliable Operation**: No false sensor readings from non-existent fields

## [0.5.0] - 2025-08-05

### ✅ **Complete Rewrite - Following Home Assistant Best Practices**

**Inspired by the official Ambient Weather Station integration**, this version simplifies and modernizes the code:

#### **New Architecture:**
- **SensorEntityDescription**: Uses modern Home Assistant sensor description pattern
- **Separated sensor types**: Weather sensors vs Info sensors with different classes
- **Clean code structure**: Follows the same patterns as official HA integrations
- **No complex unit conversions**: Uses native HA unit system (lets HA handle conversions automatically)

#### **Fixed Issues:**
- ✅ **All sensors now work reliably** - no more missing wind/rain sensors
- ✅ **Simplified unique IDs** - no more `_v2` suffixes needed
- ✅ **Proper native units** - km/h for wind, mm for rain, °C for temperature
- ✅ **Better error handling** - sensors gracefully handle connection issues

#### **Modern Standards:**
- Uses `SensorEntityDescription` (same as official integrations)
- Uses `native_unit_of_measurement` property
- Proper `device_class` and `state_class` assignments
- Clean separation between data sensors and info sensors

#### **Benefits:**
- **More reliable** - simpler code = fewer bugs
- **Future-proof** - follows HA standards that won't change
- **Easier to maintain** - clear, readable code structure
- **Better integration** - works seamlessly with HA's unit system

### Breaking Changes
- Entity unique IDs changed (old entities will become unavailable)
- New entities will be created automatically
- All functionality preserved, just with better implementation

## [0.4.2] - 2025-08-05 (Deprecated)

### Fixed
- **Improved reliability for wind and rain sensors**: Fixed conversion issues that were causing these sensors to fail
- **Better error handling**: Added fallback to default units when device settings can't be read
- **Robust unit conversion**: Enhanced `_convert_from_device_units` method to handle missing device settings
- **Enhanced logging**: Added debug logging for conversion processes and better error reporting

### Improved  
- **Device settings reading**: More reliable reading of unit settings from device with automatic retries
- **Default values**: When device unit settings are unavailable, use sensible defaults (km/h for wind, mm for rain, °C for temperature)
- **Numeric value handling**: Better parsing and conversion of numeric sensor values

### Technical
- Improved `_read_device_unit_settings` method with better error handling and defaults
- Enhanced `update()` method to retry reading device settings if needed for conversion sensors
- Added extensive debug logging for troubleshooting unit conversion issues

## [0.4.1] - 2025-08-05

### Fixed
- **Entity compatibility issue**: Fixed "La integración ws1500_legacy ya no proporciona esta entidad" error
- Updated unique IDs to `_v2` suffix to force recreation of entities after structural changes
- This resolves issues with entities like `sensor.ws1500_yearly_rain` not being recognized

### Note
- After updating to this version, old entities will be marked as unavailable and new ones will be created with `_v2` suffix
- You can safely delete the old entities from Home Assistant's entity registry
- All functionality remains the same, just with updated entity IDs

## [0.4.0] - 2025-08-05

### Added
- **Automatic unit conversion** based on Home Assistant's metric/imperial preferences
- Smart unit management that reads device settings and converts appropriately
- Support for `native_unit_of_measurement` and `native_value` properties (modern HA standard)
- Automatic conversion between:
  - Temperature: °C ↔ °F
  - Wind Speed: m/s, km/h, mph, knots, ft/s, Beaufort scale
  - Precipitation: mm ↔ inches

### Changed
- Updated sensor definitions to use native units (SI standard internally)
- Wind sensors now use m/s as native unit, displayed as km/h (metric) or mph (imperial)
- Rain sensors now use mm as native unit, displayed as mm (metric) or inches (imperial)
- Temperature sensors respect HA's temperature unit setting
- Improved device unit settings reading and caching

### Technical
- Added unit conversion helper methods
- Implemented device settings caching to reduce HTTP requests
- Added proper error handling for unit conversions
- Updated imports to include HA's unit conversion utilities

### Benefits
- **No more manual unit configuration needed** - respects your HA preferences automatically
- **Consistent display** across all weather sensors
- **Better integration** with HA's unit system
- **Future-proof** using modern HA sensor standards

## [0.3.0] - Previous Release
- Basic sensor implementation
- Device connectivity monitoring
- Configuration sensors for device settings
