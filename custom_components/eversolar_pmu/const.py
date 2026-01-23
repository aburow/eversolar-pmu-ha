"""Constants for Eversolar PMU integration."""

DOMAIN = "eversolar_pmu"

# Config keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_TIMEOUT = "timeout"
CONF_TIMEZONE = "timezone"

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
SENSOR_TIME_DELTA = "time_delta"

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
    SENSOR_TIME_DELTA: "time_delta",
}

# Attributes for diagnostic sensor
ATTR_INVERTER_ID = "inverter_id"
ATTR_MODE = "mode"
ATTR_PMU_TIME_UTC = "pmu_time_utc"
ATTR_PMU_EPOCH = "pmu_epoch"
ATTR_PMU_EPOCH_STEP = "pmu_epoch_step"
ATTR_PMU_TIME_STUCK = "pmu_time_stuck"
