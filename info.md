# Eversolar PMU Integration

Native Home Assistant integration for Eversolar solar inverter Power Management Units (PMUs).

## Features

- **Real-time Monitoring**: AC power, voltage, and frequency measurements
- **Energy Tracking**: Daily energy, lifetime energy, and operating hours
- **PV Telemetry**: String voltage, current, and calculated power
- **PMU Time Sync**: Service to synchronize PMU clock with host time
- **Device Integration**: Automatic device entity creation and grouping
- **HACS Ready**: Install directly from HACS with one-click setup

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click **Integrations**
3. Click **+ Create Custom Repository**
4. Enter: `https://github.com/aburow/eversolar-pmu-ha`
5. Select **Integration** category
6. Click **Create**
7. Search for "Eversolar PMU"
8. Click **Install**
9. Restart Home Assistant

### Manual Installation

1. Download the `custom_components/eversolar_pmu` directory
2. Copy to `<config>/custom_components/eversolar_pmu`
3. Restart Home Assistant

## Configuration

All configuration is done via the UI. After installation:

1. Go to **Settings → Devices & Services**
2. Click **Create Automation** → **Integrations**
3. Search for "Eversolar PMU"
4. Enter your inverter IP address and configure:
   - **Port** (default: 8080)
   - **Scan Interval** (default: 60 seconds, range: 10-300)
   - **Connection Timeout** (default: 5 seconds)
   - **Timezone** (for time sync operations)

## Available Sensors

| Sensor | Unit | Type | Description |
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
| PMU Time Delta | s | measurement | Diagnostic - time drift from host |

## Services

### Sync PMU Time

Synchronize the PMU's internal clock to the current host time:

```yaml
service: eversolar_pmu.sync_time
data:
  config_entry_id: "abc123def456"
```

To find your config entry ID:
1. Go to **Settings → Devices & Services → Integrations**
2. Click on the Eversolar PMU integration
3. The ID appears in the URL

## Troubleshooting

**Connection Failed:**
- Verify the inverter IP address
- Ensure the inverter is powered on
- Check that port 8080 is open
- Verify network connectivity to the inverter

**Unavailable Sensors:**
- Wait for the first poll cycle (60 seconds default)
- Check the Home Assistant logs for errors
- Verify the inverter supports all data codes

**Time Sync Issues:**
- Ensure the host system has correct time
- Check timezone configuration
- Review logs for error messages

## Differences from Command Line Sensor

If migrating from the `command_line` sensor approach:

| Old | New |
|-----|-----|
| `sensor.eversolar_*` | `sensor.eversolar_inverter_[id]_*` |
| Manual polling | Automatic polling every 60 seconds |
| JSON parsing in templates | Native sensor entities |
| No device integration | Full device with grouped entities |

## Support

For issues and feature requests, visit: https://github.com/aburow/eversolar-pmu-ha/issues

## License

See LICENSE file in repository
