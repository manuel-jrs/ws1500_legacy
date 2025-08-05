# Ambient Weather WS1500 Legacy Integration

This custom component allows you to use legacy Ambient Weather WS1500 devices locally in Home Assistant, without cloud or API fees.

## Features
- Local polling via REST
- Sensors for wind, temperature, humidity, rain, solar, etc.
- Binary sensor for device connectivity status
- Information sensors showing device configuration and units
- Device classes and state classes for best dashboard integration

## Installation
### Via HACS (Recommended)
1. Install via HACS by adding this repository as a custom repository.
2. Restart Home Assistant.
3. Go to Settings > Devices & Services > Add Integration.
4. Search for "Ambient Weather WS1500 Legacy" and add it.
5. Enter your device's IP address (e.g., `192.168.1.198`) and update interval in seconds (10-3600).

### Manual Installation
1. Copy this folder to `custom_components/ws1500_legacy` in your Home Assistant config.
2. Restart Home Assistant.
3. Add via UI (Settings > Devices & Services) or via YAML:

```yaml
sensor:
  - platform: ws1500_legacy
    host: 192.168.1.198
    scan_interval: 60
```

## Available Sensors

### Weather Sensors
All sensors include appropriate device classes and state classes for proper dashboard integration:
- **Temperature**: Indoor and outdoor temperature
- **Humidity**: Indoor and outdoor humidity levels  
- **Wind**: Wind speed, gust speed, and direction
- **Rain**: Rainfall rate and total accumulation
- **Pressure**: Absolute and relative barometric pressure
- **Solar**: Solar radiation measurement
- **UV**: UV index
- **Dew Point**: Dew point temperature
- **Wind Chill**: Wind chill temperature

### System Sensors  
- **Device Status**: Binary sensor indicating if the weather station is online/reachable
- **Device IP**: Shows the IP address of your weather station
- **Time Zone**: Shows the current time zone setting (e.g., "UTC-6")
- **Daylight Saving**: Shows if daylight saving time is enabled ("on" or "off")
- **Last Update**: Shows when sensors were last updated
- **Unit Sensors**: Shows the configured units for each measurement type:
  - **Wind Unit**: km/h, m/s, mph, knot, etc.
  - **Rain Unit**: mm or in
  - **Pressure Unit**: hPa, inHg, or mmHg  
  - **Temperature Unit**: °C or °F
  - **Solar Unit**: W/m², lux, or fc

## Technical Details

### Device Endpoints
This integration accesses the following URLs on your WS1500 device:

- **`http://<IP>/livedata.htm`**: Main weather data source
  - Used for: All weather sensors (temperature, humidity, wind, rain, solar, UV, pressure, etc.)
  - Polling frequency: Based on your configured update interval
  - Data format: HTML form with input fields containing sensor values

- **`http://<IP>/station.htm`**: Device configuration page
  - Used for: Time zone, daylight saving, and unit configuration sensors
  - Polling frequency: Same as weather data (updates whenever sensors refresh)
  - Data format: HTML form with select dropdowns and input fields

### Data Extraction
- Weather data is extracted using regex patterns from HTML input field values
- Configuration data is extracted by finding selected options in HTML select elements
- All HTTP requests use a 10-second timeout for reliability
- Failed requests are logged and sensor states are set to `None` or `unknown`

## Notes
- This integration is for legacy Ambient Weather devices (WS1500, etc.)
- For newer models, use official or other community integrations.
- No cloud required, all data stays local.
- Device settings can be changed directly on the device web interface if needed.
