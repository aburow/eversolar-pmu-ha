"""Constants for Eversolar PMU integration."""

DOMAIN = "eversolar_pmu"

# Config keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_TIMEOUT = "timeout"
CONF_TIMEZONE = "timezone"
CONF_AUTO_SYNC_ENABLED = "auto_sync_enabled"
CONF_AUTO_SYNC_DELAY = "auto_sync_delay"
CONF_PV_VOLTAGE_THRESHOLD = "pv_voltage_threshold"
CONF_PV_VOLTAGE_STATS_CUTOFF = "pv_voltage_stats_cutoff"

# Defaults
DEFAULT_PORT = 8080
DEFAULT_SCAN_INTERVAL = 60
DEFAULT_TIMEOUT = 5.0
DEFAULT_TIMEZONE = "Australia/Brisbane"

# Sensor types
SENSOR_POWER = "power"
SENSOR_VOLTAGE = "voltage"
SENSOR_FREQUENCY = "frequency"
SENSOR_ENERGY_TODAY = "energy_today"
SENSOR_ENERGY_TOTAL = "energy_total"
SENSOR_HOURS_TOTAL = "hours_total"
SENSOR_PV_VOLTAGE = "pv_voltage"
SENSOR_PV_CURRENT = "pv_current"
SENSOR_PV_POWER = "pv_power"

# Sensor data keys (map to JSON response keys)
SENSOR_DATA_KEYS = {
    SENSOR_POWER: "power_w",
    SENSOR_VOLTAGE: "vac_v",
    SENSOR_FREQUENCY: "fac_hz",
    SENSOR_ENERGY_TODAY: "e_today_kwh",
    SENSOR_ENERGY_TOTAL: "e_total_kwh",
    SENSOR_HOURS_TOTAL: "h_total_hours",
    SENSOR_PV_VOLTAGE: "pv_v",
    SENSOR_PV_CURRENT: "pv_a",
    SENSOR_PV_POWER: "pv_w_est",
}

# Attributes for diagnostic sensor
ATTR_INVERTER_ID = "inverter_id"
ATTR_MODE = "mode"
ATTR_PMU_TIME_UTC = "pmu_time_utc"
ATTR_PMU_EPOCH = "pmu_epoch"
ATTR_PMU_EPOCH_STEP = "pmu_epoch_step"
ATTR_PMU_TIME_STUCK = "pmu_time_stuck"

# Error Message Bit Flags (Table 3-7)
ERROR_MESSAGES = {
    31: "Master-Slave-Fail",
    30: "EEPROM-Fail",
    29: "Fac-Master-Fail",
    28: "Fac-Slave-Fail",
    25: "Rly1-Fail",
    23: "ENS-Vac-Fail",
    22: "ENS-Fac-Fail",
    20: "ENS-Mess-Fail",
    19: "Offset-Iac-Fail",
    18: "Zpv-PE-Fail",
    17: "Vac-Master-Fail",
    16: "FanLock-Warning",
    15: "VpvMax-Fail",
    13: "Temperature-Fail",
    12: "M-S Version Fail",
    11: "Bus-Fail",
    10: "GFCI-Fail",
    9: "No-Utility",
    7: "Device Fault",
    6: "Bus_High-Fail",
    4: "ENS-GFCI-Fault",
    3: "ENS-DCI-Fault",
    2: "Ref 2.5V Fault",
    1: "DC Sensor Fault",
    0: "GFCI Failure",
}
