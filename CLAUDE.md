# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Home Assistant custom integration for the legacy Ambient Weather **WS1500** (Fine Offset) weather station. Polls the device's local HTTP web UI — there is no JSON API, no cloud, no auth. Distributed via HACS (`hacs.json`) and manifest-installable from `custom_components/ws1500_legacy/`.

Target: Home Assistant `2023.0.0+`. Single runtime dep: `aiohttp>=3.8.0` (already provided by HA core).

## Architecture

The integration is a thin scraper sitting behind one `DataUpdateCoordinator`. Reading these in order is enough to understand the whole system:

1. **`coordinator.py` — `WS1500LegacyCoordinator`**: fetches and parses both device pages, converts to SI, exposes a single dict `{"sensors": {...}, "info": {...}}` to all platforms. Holds a 30s cache for station settings (`_station_cache`) and pre-compiles all regex patterns at init. Also owns `async_reboot_device()` and `get_device_info()`.
2. **`const.py`**: the integration's source of truth — domain constants, all regex patterns (`SENSOR_DATA_MAPPING`, `INFO_SENSOR_MAPPING`, `*_UNIT_PATTERN`), unit-code→string maps (`WIND_UNITS` etc.), and the pure unit-conversion functions (`convert_temperature`, `convert_wind_speed`, …). Sensors are bucketed into `TEMPERATURE_SENSORS` / `WIND_SENSORS` / `RAIN_SENSORS` / `PRESSURE_SENSORS` / `SOLAR_SENSORS` `frozenset`s — those buckets drive `_convert_units()` in the coordinator.
3. **Three HA platforms**, each subscribing to the coordinator:
   - `sensor.py` — weather sensors (`SENSOR_DESCRIPTIONS`) and diagnostic info sensors (`INFO_SENSOR_DESCRIPTIONS`). Both use `SensorEntityDescription`.
   - `binary_sensor.py` — single connectivity sensor whose `is_on` mirrors `coordinator.last_update_success`.
   - `button.py` — reboot button that calls `coordinator.async_reboot_device()` and posts a `persistent_notification`.
4. **`config_flow.py`**: UI setup (`async_step_user`) and options flow (`async_step_init`). `validate_host()` does a live GET against `/livedata.htm` and confirms it sees `name="outTemp"` or `name="windir"` before accepting the host. Options take priority over data on reload (`__init__.async_setup_entry`), enabling reconfiguration.

### How the device is read

| Endpoint | Purpose | Cached |
|---|---|---|
| `http://<host>/livedata.htm` | All weather sensors + a few info fields (`Outdoor1ID`, `outBattSta1`, `CurrTime`) | scan_interval (default 60s) |
| `http://<host>/station.htm` | Timezone, DST, configured units (wind/rain/pressure/temp/solar) | 30s (`CACHE_DURATION`) |
| `http://<host>/msgreboot.htm` | Reboot trigger | n/a |

Both are HTML; values are pulled with regex against `name="..." value="..."` for inputs, and `<option value="N" selected` inside the relevant `<select name="...">` for dropdowns.

### Unit handling

Internal storage is **always SI**: °C, km/h, mm, hPa, W/m². Pipeline:

1. Parse station.htm → resolve the device's currently-configured unit codes via `WIND_UNITS` / `RAIN_UNITS` / etc.
2. Parse livedata.htm → raw float values in **device units**.
3. `_convert_units()` looks up each sensor key in the category `frozenset`s and applies the matching converter.
4. Entities expose `native_unit_of_measurement` as the SI unit and let HA do the user-facing metric/imperial conversion.

When `_fetch_station_data()` fails it falls back to the cached dict, then to `DEFAULT_STATION_DATA` — never raises. This keeps weather sensors flowing even if `/station.htm` is briefly unreachable.

### Unavailable / missing sensors

Devices return sentinel strings (`----`, `--`, `--.-`, `0x--`, `- -`) for hardware that isn't physically connected (e.g. indoor temp probe missing). These are listed in `UNAVAILABLE_VALUES` and become `None`. The entity's `available` property checks `native_value is not None`, so HA marks them `unknown` rather than reporting bogus zeros.

### YAML vs config-flow setup paths

Both setup paths are supported. The YAML path (`async_setup_platform` in `sensor.py` and `binary_sensor.py`) uses a **per-host `asyncio.Lock`** stored in `hass.data[DOMAIN]` keyed by `yaml_lock_<host>` so the sensor and binary_sensor platforms initializing in parallel share **one** coordinator instance. The UI path stores the coordinator under `entry.entry_id`. Don't simplify this lock away — it prevents duplicate coordinators (and duplicate polling) on YAML setup.

## Conventions worth preserving

- **Unique IDs** are `ws1500_legacy_<sensor_key>`. Avoid changing them without bumping a version note in `CHANGELOG.md` — older versions used a `_v2` suffix specifically because re-keying invalidates user dashboards (see `0.4.1`).
- **Wind direction** uses `SensorStateClass.MEASUREMENT_ANGLE` (not `MEASUREMENT`). This is intentional and documented as a fix in `0.6.0`.
- **`lastrain` does not exist** on real WS1500 hardware. The "last rain date" sensor was removed in 0.6.0 after device validation. Don't reintroduce it from `SMART_SENSORS_README.md` (which documents the removed feature) without re-verifying against a live device.
- New sensors: add the regex to `SENSOR_DATA_MAPPING` in `const.py`, add the entity to the relevant unit-conversion `frozenset` if needed, and append a `SensorEntityDescription` to `SENSOR_DESCRIPTIONS` in `sensor.py`. The coordinator picks it up automatically.

## Common tasks

```bash
# Validate the static sensor configuration table (device_class + state_class combinations)
python validate_sensors.py

# Probe a live device's livedata.htm and report which mappings hit
# Edit HOST inside the file first.
python test_sensor_mapping.py
```

There is **no pytest suite, no linter config, and no CI**. The `test_*.py` files in the repo root are ad-hoc validation scripts that talk to a real device on the LAN — several are empty stubs (`test_optimization.py`, `test_udp_protocol.py`, `udp_listener.py`). Don't assume them as a test framework.

To install locally for testing: copy `custom_components/ws1500_legacy/` into a Home Assistant config directory and restart HA. There is no build step.

## Repo layout notes

- `custom_components/ws1500_legacy/translations/` — `en.json` and `es.json` are committed and ship via HACS. The repo's `.gitignore` is empty.
- The Spanish-language docs (`SMART_SENSORS_README.md`, `ejemplos_automatizacion_last_rain.md`) describe the removed last-rain feature and are stale relative to the current code.
- `manifest.json` `version` is the source of truth for the integration version exposed to HA; `CHANGELOG.md` tracks user-visible changes per release.
