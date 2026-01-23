# Eversolar PMU Home Assistant Integration

A native Home Assistant custom integration for Eversolar solar inverter Power Management Units (PMUs).

## Features

- **Real-time Monitoring**: AC power, voltage, and frequency measurements
- **Energy Tracking**: Daily energy, lifetime energy, and operating hours
- **PV Telemetry**: String voltage, current, and calculated power
- **PMU Time Sync**: Service to synchronize PMU clock with host time
- **Device Integration**: Automatic device entity creation and grouping
- **HACS Ready**: Install directly from HACS with one-click setup
- **No External Dependencies**: Uses Python stdlib only

## Quick Start

### Installation via HACS (Recommended)

1. Open Home Assistant and go to **HACS**
2. Click **Integrations**
3. Click the three-dot menu → **Custom repositories**
4. Add this repository URL: `http://192.168.100.114:3000/home/eversolar-pmu-ha`
5. Category: **Integration**
6. Click **Create**
7. Search for "Eversolar PMU"
8. Click **Install**
9. Restart Home Assistant

### Manual Installation

1. Download this repository
2. Copy `custom_components/eversolar_pmu/` to your Home Assistant `custom_components/` directory
3. Restart Home Assistant

### Configuration

After installation:

1. Go to **Settings → Devices & Services**
2. Click **Create Integration**
3. Search for "Eversolar PMU"
4. Enter your inverter IP address (e.g., 192.168.0.190)
5. Configure optional settings:
   - **Port**: TCP port (default: 8080)
   - **Scan Interval**: Polling interval in seconds (default: 60, range: 10-300)
   - **Timeout**: Connection timeout in seconds (default: 5.0)
   - **Timezone**: For time sync operations (default: Australia/Brisbane)
6. Submit

## Sensors

The integration creates 10 sensor entities:

| Entity | Unit | Type | Description |
|--------|------|------|-------------|
| Power | W | measurement | Current AC power output |
| AC Voltage | V | measurement | AC output voltage |
| AC Frequency | Hz | measurement | Grid frequency |
| Energy Today | kWh | total | Energy generated today |
| Total Energy | kWh | total_increasing | Lifetime energy generation |
| Operation Hours | h | total_increasing | Total operating hours |
| PV Voltage | V | measurement | Solar string voltage |
| PV Current | A | measurement | Solar string current |
| PV Power | W | measurement | Calculated solar power |
| PMU Time Delta | s | measurement | Time drift from host (diagnostic) |

All sensors are automatically grouped under a single device named "Eversolar Inverter [SERIAL_ID]".

## Services

### eversolar_pmu.sync_time

Synchronize the PMU's internal clock to the current host time.

**Service Data:**
- `config_entry_id` (required): The config entry ID from Settings → Devices & Services

**Example Automation:**
```yaml
automation:
  - alias: Sync Eversolar Time Daily
    trigger:
      at: "02:00:00"
    action:
      service: eversolar_pmu.sync_time
      data:
        config_entry_id: "abc123def456"
```

## Troubleshooting

### Integration won't add / "Cannot Connect" error

**Check network connectivity:**
```bash
ping 192.168.0.190
nc -zv 192.168.0.190 8080
```

**Verify inverter:**
- Ensure the inverter is powered on
- Check that port 8080 is accessible
- Try with a longer timeout in the config

### Sensors show "Unavailable"

- Wait 60+ seconds for the first poll cycle
- Check Home Assistant logs for error messages
- Verify network connectivity to the inverter

### Values seem incorrect

1. Compare with the original script:
   ```bash
   # Clone the main repository
   git clone https://github.com/anthropics/eversolar-pmu.git
   cd eversolar-pmu
   python3 eversolar_pmu_poll_dynamic.py --host 192.168.0.190
   ```

2. Check the protocol documentation: https://github.com/anthropics/eversolar-pmu

3. Enable debug logging in Home Assistant:
   ```yaml
   logger:
     logs:
       custom_components.eversolar_pmu: debug
   ```

### Time sync not working

- Verify your Home Assistant system time is correct
- Check that the timezone setting matches your region
- Review Home Assistant logs for error messages

## Entity IDs

Entity IDs follow the pattern:
```
sensor.eversolar_inverter_[INVERTER_ID]_[SENSOR_NAME]
```

Example (Inverter ID: B885400A129C0030):
```
sensor.eversolar_inverter_b885400a129c0030_power
sensor.eversolar_inverter_b885400a129c0030_ac_voltage
sensor.eversolar_inverter_b885400a129c0030_ac_frequency
sensor.eversolar_inverter_b885400a129c0030_energy_today
sensor.eversolar_inverter_b885400a129c0030_total_energy
sensor.eversolar_inverter_b885400a129c0030_total_operation_hours
sensor.eversolar_inverter_b885400a129c0030_pv_voltage
sensor.eversolar_inverter_b885400a129c0030_pv_current
sensor.eversolar_inverter_b885400a129c0030_pv_power
sensor.eversolar_inverter_b885400a129c0030_pmu_time_delta
```

## Multiple Inverters

You can add multiple instances of this integration for different inverters:

1. Settings → Devices & Services → Create Integration
2. Search "Eversolar PMU"
3. Enter different inverter IP address
4. Each instance will create its own device and sensors

## Configuration Examples

### Basic Setup (Defaults)
```
Host: 192.168.0.190
Port: 8080
Scan Interval: 60
Timeout: 5.0
Timezone: Australia/Brisbane
```

### Fast Polling
```
Host: 192.168.0.190
Port: 8080
Scan Interval: 30
Timeout: 5.0
Timezone: Australia/Brisbane
```

### Slow/Network-Constrained
```
Host: 192.168.0.190
Port: 8080
Scan Interval: 120
Timeout: 10.0
Timezone: Australia/Brisbane
```

## Advanced Usage

### Using Sensors in Automations

```yaml
automation:
  - alias: High Power Alert
    trigger:
      - platform: numeric_state
        entity_id: sensor.eversolar_inverter_b885400a129c0030_power
        above: 5000
    action:
      - service: notify.notify
        data:
          message: "High power generation: {{ states('sensor.eversolar_inverter_b885400a129c0030_power') }}W"
```

### Creating Template Sensors

```yaml
template:
  - sensor:
      - name: "Eversolar Daily Efficiency"
        unit_of_measurement: "%"
        state: >
          {% set energy = states('sensor.eversolar_inverter_b885400a129c0030_energy_today') | float(0) %}
          {% set pv_power = states('sensor.eversolar_inverter_b885400a129c0030_pv_power') | float(0) %}
          {{ ((energy / 24 / (pv_power / 1000)) * 100) | round(1) if pv_power > 0 else 'unavailable' }}
```

### Dashboard Card Example

```yaml
type: entities
title: Eversolar Inverter
entities:
  - entity: sensor.eversolar_inverter_b885400a129c0030_power
    name: Current Power
  - entity: sensor.eversolar_inverter_b885400a129c0030_ac_voltage
    name: AC Voltage
  - entity: sensor.eversolar_inverter_b885400a129c0030_energy_today
    name: Today's Energy
  - entity: sensor.eversolar_inverter_b885400a129c0030_total_energy
    name: Total Energy
```

## Documentation

- **[QUICK_START.md](QUICK_START.md)** - Quick reference and examples
- **[info.md](info.md)** - Feature overview for HACS UI

For comprehensive integration development documentation, see the main project:
https://github.com/anthropics/eversolar-pmu

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/anthropics/eversolar-pmu-ha/issues

For protocol questions and script usage:
- Main Project: https://github.com/anthropics/eversolar-pmu

## License

This project is part of the Eversolar PMU project. See LICENSE file for details.

## Related Projects

- **[eversolar-pmu](https://github.com/anthropics/eversolar-pmu)** - Main project with standalone Python script, protocol documentation, and detailed implementation guides
- **[eversolar-pmu-ha](https://github.com/anthropics/eversolar-pmu-ha)** - This repository (Home Assistant integration only)

---

**Version**: 1.1.2
**Status**: Production Ready ✅
**Home Assistant**: 2021.12.0+
**Python**: 3.9+
