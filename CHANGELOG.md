# Changelog

All notable changes to this project will be documented in this file.

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
