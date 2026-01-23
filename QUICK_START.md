# Eversolar PMU Home Assistant Integration - Quick Start

## For Home Assistant Users

### Installation (HACS - Recommended)

1. **Add Custom Repository**
   - Open Home Assistant
   - Settings → Devices & Services → HACS
   - Click three-dot menu → Custom repositories
   - URL: `https://github.com/anthropics/eversolar-pmu`
   - Category: Integration
   - Click Create

2. **Install Integration**
   - HACS → Integrations → Search "Eversolar PMU"
   - Click Install
   - Restart Home Assistant

3. **Configure Integration**
   - Settings → Devices & Services → Create Integration
   - Search "Eversolar PMU"
   - Enter your inverter IP address
   - Configure other settings (optional):
     - Port: 8080 (default)
     - Scan Interval: 60 seconds (10-300)
     - Timeout: 5.0 seconds
     - Timezone: Australia/Brisbane
   - Submit

4. **Use Sensors**
   - All sensors appear under device: "Eversolar Inverter [ID]"
   - Use in automations, templates, and dashboards
   - Call service `eversolar_pmu.sync_time` to sync PMU time

### Troubleshooting

**Integration won't add:**
- Verify inverter IP with: `ping 192.168.0.190`
- Check port 8080 is open: `nc -zv 192.168.0.190 8080`
- Ensure inverter is powered on

**Sensors show Unavailable:**
- Wait 60+ seconds for first poll
- Check Home Assistant logs
- Verify network connectivity

**Values seem incorrect:**
- Compare with original script:
  ```bash
  python3 eversolar_pmu_poll_dynamic.py --host 192.168.0.190
  ```
- Check protocol documentation in [EVERSOLAR_PROTOCOL_EXPERT.md](EVERSOLAR_PROTOCOL_EXPERT.md)

---

## For Developers

### Project Structure

```
custom_components/eversolar_pmu/
├── __init__.py              # Integration setup
├── config_flow.py           # UI configuration
├── const.py                 # Constants
├── coordinator.py           # Data polling
├── eversolar_protocol.py    # Protocol implementation
├── sensor.py                # Sensor entities
├── manifest.json            # Metadata
├── strings.json             # UI strings
├── services.yaml            # Service docs
└── translations/en.json     # Translations
```

### Key Components

**eversolar_protocol.py**
- `EversolarPMU` class: Main protocol implementation
- `test_connection()`: Verify inverter reachable
- `connect_and_poll()`: Get all sensor data
- `sync_time()`: Sync PMU clock

**coordinator.py**
- `EversolarDataUpdateCoordinator`: Polls PMU on schedule
- Non-blocking executor jobs
- Error handling with automatic retry

**config_flow.py**
- `EversolarConfigFlow`: User setup UI
- `EversolarOptionsFlow`: Update settings

**sensor.py**
- 10 sensor entities
- Proper device integration
- Device class assignments

**__init__.py**
- Integration setup
- Service registration
- Config entry management

### Running Tests

```bash
# Test protocol functions
python3 test_protocol.py

# Test full integration (requires Home Assistant)
python3 test_integration.py
```

### Adding a New Sensor

1. Add constant to `const.py`:
   ```python
   SENSOR_MY_VALUE = "my_value"
   SENSOR_DATA_KEYS = {
       SENSOR_MY_VALUE: "my_value_json_key",
   }
   ```

2. Add entity to `sensor.py`:
   ```python
   EversolarSensor(
       coordinator,
       SENSOR_MY_VALUE,
       "My Value Name",
       "my_value_json_key",
       SensorDeviceClass.POWER,
       "unit",
       SensorStateClass.MEASUREMENT,
   ),
   ```

3. Restart Home Assistant

### Debugging

Enable debug logging in `configuration.yaml`:
```yaml
logger:
  logs:
    custom_components.eversolar_pmu: debug
```

### Documentation

- **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** - Comprehensive developer guide
- **[INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md)** - Implementation overview
- **[EVERSOLAR_PROTOCOL_EXPERT.md](EVERSOLAR_PROTOCOL_EXPERT.md)** - Protocol specification
- **[info.md](info.md)** - User documentation for HACS

---

## Entity IDs

Format: `sensor.eversolar_inverter_[inverter_id]_[sensor_name]`

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

---

## Services

### eversolar_pmu.sync_time

Synchronize PMU internal clock to host time.

**Example Automation:**
```yaml
automation:
  - alias: Sync Eversolar Time Daily
    trigger:
      at: "02:00:00"
    action:
      service: eversolar_pmu.sync_time
      data:
        config_entry_id: "your_entry_id"
```

**Example Script Call:**
```yaml
action:
  service: eversolar_pmu.sync_time
  data:
    config_entry_id: "abc123def456"
```

---

## Config Entry ID

Find your config entry ID:
1. Settings → Devices & Services → Integrations
2. Click on "Eversolar PMU"
3. URL shows: `/integrations/eversolar_pmu/your_id_here`
4. Use that ID in service calls

---

## Migration from Command Line Sensor

If upgrading from old approach:

1. **Remove old configuration from `configuration.yaml`:**
   ```yaml
   # REMOVE:
   command_line:
     - sensor:
         name: "Eversolar..."
         command: "python3..."

   template:
     - sensor:
         name: "Eversolar..."
   ```

2. **Restart Home Assistant**

3. **Install new integration (see above)**

4. **Update automations/dashboards:**
   - Old: `sensor.eversolar_inverter_power`
   - New: `sensor.eversolar_inverter_[id]_power`

5. **Verify data:**
   - Compare values before/after
   - Check graphs for continuity

---

## Useful Commands

### Check Inverter Connection
```bash
python3 -c "
from custom_components.eversolar_pmu.eversolar_protocol import EversolarPMU
if EversolarPMU.test_connection('192.168.0.190', 8080):
    print('✓ Connected')
else:
    print('✗ Not reachable')
"
```

### Get Raw Data
```bash
python3 eversolar_pmu_poll_dynamic.py --host 192.168.0.190 | jq '.'
```

### Check Integration Status
In Home Assistant Developer Tools → Python REPL:
```python
domain = "eversolar_pmu"
entry_id = "your_entry_id"
coordinator = hass.data[domain][entry_id]
print(f"Inverter: {coordinator.inverter_id}")
print(f"Data: {coordinator.data}")
print(f"Last update: {coordinator.last_update_success}")
```

---

## FAQ

**Q: Do I need the original script?**
A: No, the integration is standalone. The script is included for reference/testing only.

**Q: Can I have multiple inverters?**
A: Yes, add multiple config entries, each for a different IP address.

**Q: What Python version do I need?**
A: Home Assistant requires Python 3.9+ (stdlib includes `zoneinfo`).

**Q: Can I use this without Home Assistant?**
A: Yes, the original script (`eversolar_pmu_poll_dynamic.py`) works standalone.

**Q: What if my timezone isn't in the list?**
A: The config flow includes a text input for custom timezones (like `America/New_York`).

**Q: How do I report bugs?**
A: GitHub Issues: https://github.com/anthropics/eversolar-pmu/issues

---

## Support Resources

- **User Guide**: [info.md](info.md)
- **Developer Guide**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- **Protocol Spec**: [EVERSOLAR_PROTOCOL_EXPERT.md](EVERSOLAR_PROTOCOL_EXPERT.md)
- **Home Assistant Docs**: https://developers.home-assistant.io/

---

**Last Updated**: 2026-01-23
**Integration Version**: 1.1.2
**Status**: Production Ready ✅
