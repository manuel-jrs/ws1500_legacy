# Ambient Weather WS1500 Legacy Integration

This custom component allows you to use legacy Ambient Weather WS1500 devices locally in Home Assistant, without cloud or API fees.

## Features
- Local polling via REST
- Sensors for wind, temperature, humidity, rain, solar, etc.
- Device classes and state classes for best dashboard integration

## Installation
1. Copy this folder to `custom_components/ws1500_legacy` in your Home Assistant config.
2. Add your configuration to `configuration.yaml`:

```yaml
sensor:
  - platform: ws1500_legacy
    resource: http://192.168.1.198/livedata.htm
    scan_interval: 60
```

## Notes
- This integration is for legacy Ambient Weather devices (WS1500, etc.)
- For newer models, use official or other community integrations.
- No cloud required, all data stays local.
