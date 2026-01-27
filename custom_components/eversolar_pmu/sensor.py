# SPDX-License-Identifier: GPL-3.0
# Copyright (C) 2026 Anthony Burow
# https://github.com/aburow/eversolar-pmu-ha

"""Sensor platform for Eversolar PMU."""
import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    EntityCategory,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_INVERTER_ID,
    ATTR_MODE,
    ATTR_PMU_EPOCH,
    ATTR_PMU_EPOCH_STEP,
    ATTR_PMU_TIME_STUCK,
    ATTR_PMU_TIME_UTC,
    CONF_PV_VOLTAGE_STATS_CUTOFF,
    CONF_PV_VOLTAGE_THRESHOLD,
    DOMAIN,
    ERROR_MESSAGES,
    SENSOR_DATA_KEYS,
    SENSOR_ENERGY_TODAY,
    SENSOR_ENERGY_TOTAL,
    SENSOR_FREQUENCY,
    SENSOR_HOURS_TOTAL,
    SENSOR_POWER,
    SENSOR_PV_CURRENT,
    SENSOR_PV_POWER,
    SENSOR_PV_VOLTAGE,
    SENSOR_VOLTAGE,
)
from .coordinator import EversolarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor platform from a config entry."""
    coordinator: EversolarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EversolarSensor(
            coordinator,
            SENSOR_POWER,
            "Power",
            "power_w",
            SensorDeviceClass.POWER,
            "W",
            SensorStateClass.MEASUREMENT,
        ),
        EversolarSensor(
            coordinator,
            SENSOR_VOLTAGE,
            "AC Voltage",
            "vac_v",
            SensorDeviceClass.VOLTAGE,
            "V",
            SensorStateClass.MEASUREMENT,
        ),
        EversolarSensor(
            coordinator,
            SENSOR_FREQUENCY,
            "AC Frequency",
            "fac_hz",
            SensorDeviceClass.FREQUENCY,
            "Hz",
            SensorStateClass.MEASUREMENT,
        ),
        EversolarSensor(
            coordinator,
            SENSOR_ENERGY_TODAY,
            "Energy Today",
            "e_today_kwh",
            SensorDeviceClass.ENERGY,
            "kWh",
            SensorStateClass.TOTAL,
        ),
        EversolarSensor(
            coordinator,
            SENSOR_ENERGY_TOTAL,
            "Total Energy",
            "e_total_kwh",
            SensorDeviceClass.ENERGY,
            "kWh",
            SensorStateClass.TOTAL_INCREASING,
        ),
        EversolarSensor(
            coordinator,
            SENSOR_HOURS_TOTAL,
            "Total Operation Hours",
            "h_total_hours",
            None,
            "h",
            SensorStateClass.TOTAL_INCREASING,
        ),
        EversolarSensor(
            coordinator,
            SENSOR_PV_VOLTAGE,
            "PV Voltage",
            "pv_v",
            SensorDeviceClass.VOLTAGE,
            "V",
            SensorStateClass.MEASUREMENT,
        ),
        EversolarSensor(
            coordinator,
            SENSOR_PV_CURRENT,
            "PV Current",
            "pv_a",
            SensorDeviceClass.CURRENT,
            "A",
            SensorStateClass.MEASUREMENT,
        ),
        EversolarSensor(
            coordinator,
            SENSOR_PV_POWER,
            "PV Power",
            "pv_w_est",
            SensorDeviceClass.POWER,
            "W",
            SensorStateClass.MEASUREMENT,
        ),
        EversolarACOnlineTimestamp(
            coordinator,
            "ac_online_time",
            "AC Online Time",
            "ac_online_time",
        ),
        EversolarACOfflineTimestamp(
            coordinator,
            "ac_offline_time",
            "AC Offline Time",
            "ac_offline_time",
        ),
        EversolarOperationModeSensor(coordinator),
        EversolarErrorMessageSensor(coordinator),
        EversolarDailyEfficiencySensor(coordinator),
    ]

    async_add_entities(entities)


class EversolarSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Eversolar sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EversolarDataUpdateCoordinator,
        sensor_type: str,
        name: str,
        data_key: str,
        device_class: Optional[SensorDeviceClass],
        unit: str,
        state_class: SensorStateClass,
    ) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._data_key = data_key

        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_state_class = state_class

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_{self._sensor_type}"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_{self._sensor_type}"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        # If coordinator is unavailable, entity is unavailable
        if not super().available:
            return False

        # If inverter is fully down, mark power-related sensors as unavailable
        if self.coordinator.is_fully_down:
            unavailable_types = {
                SENSOR_POWER,
                SENSOR_VOLTAGE,
                SENSOR_FREQUENCY,
                SENSOR_ENERGY_TODAY,
                SENSOR_PV_VOLTAGE,
                SENSOR_PV_CURRENT,
                SENSOR_PV_POWER,
            }
            if self._sensor_type in unavailable_types:
                return False

        # If PV voltage is below stats cutoff, mark statistics as unreliable
        if self.coordinator.is_below_stats_cutoff:
            stats_types = {
                SENSOR_ENERGY_TODAY,
                SENSOR_ENERGY_TOTAL,
                SENSOR_HOURS_TOTAL,
                SENSOR_POWER,
                SENSOR_PV_POWER,
            }
            if self._sensor_type in stats_types:
                return False

        return True

    @property
    def native_value(self) -> Optional[Any]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._data_key)

    @property
    def device_info(self) -> dict:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.inverter_id or self.coordinator.config_entry.entry_id)},
            "name": f"Eversolar Inverter {self.coordinator.inverter_id or 'Unknown'}",
            "manufacturer": "Eversolar",
            "model": "PMU (TCP/IP)",
        }


class EversolarDiagnosticSensor(EversolarSensor):
    """Diagnostic sensor with additional attributes."""

    _attr_entity_registry_enabled_default = True

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        if not self.coordinator.data:
            return {}

        attrs = {}
        if self.coordinator.inverter_id:
            attrs[ATTR_INVERTER_ID] = self.coordinator.inverter_id
        if ATTR_MODE in self.coordinator.data:
            attrs[ATTR_MODE] = self.coordinator.data.get("mode")
        if self.coordinator.data.get("pmu_time_utc"):
            attrs[ATTR_PMU_TIME_UTC] = self.coordinator.data.get("pmu_time_utc")
        if self.coordinator.data.get("pmu_epoch") is not None:
            attrs[ATTR_PMU_EPOCH] = self.coordinator.data.get("pmu_epoch")
        if self.coordinator.data.get("pmu_epoch_step") is not None:
            attrs[ATTR_PMU_EPOCH_STEP] = self.coordinator.data.get("pmu_epoch_step")
        if self.coordinator.data.get("pmu_time_stuck") is not None:
            attrs[ATTR_PMU_TIME_STUCK] = self.coordinator.data.get("pmu_time_stuck")

        return attrs


class EversolarACOnlineTimestamp(CoordinatorEntity, SensorEntity):
    """AC Online Timestamp sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: EversolarDataUpdateCoordinator, sensor_type: str, name: str, data_key: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._data_key = data_key
        self._attr_name = name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_ac_online_time"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_ac_online_time"

    @property
    def native_value(self) -> Optional[Any]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._data_key)

    @property
    def device_info(self) -> dict:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.inverter_id or self.coordinator.config_entry.entry_id)},
            "name": f"Eversolar Inverter {self.coordinator.inverter_id or 'Unknown'}",
            "manufacturer": "Eversolar",
            "model": "PMU (TCP/IP)",
        }


class EversolarACOfflineTimestamp(CoordinatorEntity, SensorEntity):
    """AC Offline Timestamp sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: EversolarDataUpdateCoordinator, sensor_type: str, name: str, data_key: str) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._sensor_type = sensor_type
        self._data_key = data_key
        self._attr_name = name

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_ac_offline_time"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_ac_offline_time"

    @property
    def native_value(self) -> Optional[Any]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get(self._data_key)

    @property
    def device_info(self) -> dict:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.inverter_id or self.coordinator.config_entry.entry_id)},
            "name": f"Eversolar Inverter {self.coordinator.inverter_id or 'Unknown'}",
            "manufacturer": "Eversolar",
            "model": "PMU (TCP/IP)",
        }


class EversolarOperationModeSensor(CoordinatorEntity, SensorEntity):
    """Operation Mode sensor."""

    _attr_has_entity_name = True
    _attr_name = "Operation Mode"

    def __init__(self, coordinator: EversolarDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_operation_mode"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_operation_mode"

    @property
    def native_value(self) -> Optional[str]:
        """Return the operation mode state."""
        if not self.coordinator.data:
            return None
        mode = self.coordinator.data.get("mode")
        if mode is None:
            return None

        mode_map = {
            0x0000: "Wait",
            0x0001: "Normal",
            0x0002: "Fault",
            0x0003: "Permanent Fault",
        }
        return mode_map.get(mode, "Unknown")

    @property
    def device_info(self) -> dict:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.inverter_id or self.coordinator.config_entry.entry_id)},
            "name": f"Eversolar Inverter {self.coordinator.inverter_id or 'Unknown'}",
            "manufacturer": "Eversolar",
            "model": "PMU (TCP/IP)",
        }


class EversolarErrorMessageSensor(CoordinatorEntity, SensorEntity):
    """Error Message Bit Flags sensor."""

    _attr_has_entity_name = True
    _attr_name = "Error Messages"

    def __init__(self, coordinator: EversolarDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_error_messages"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_error_messages"

    @property
    def native_value(self) -> Optional[str]:
        """Return the active error messages."""
        if not self.coordinator.data:
            return None
        error_flags = self.coordinator.data.get("error_flags")
        if error_flags is None:
            return "No errors"

        if error_flags == 0:
            return "No errors"

        active_errors = []
        for bit_pos, error_name in ERROR_MESSAGES.items():
            if error_flags & (1 << bit_pos):
                active_errors.append(error_name)

        if not active_errors:
            return "No errors"

        return ", ".join(active_errors)

    @property
    def extra_state_attributes(self) -> dict:
        """Return error flags as attributes."""
        if not self.coordinator.data:
            return {}

        error_flags = self.coordinator.data.get("error_flags")
        if error_flags is None:
            return {}

        attrs = {
            "error_flags_hex": f"0x{error_flags:08x}",
            "error_flags_int": error_flags,
        }

        # Add individual bit states
        for bit_pos, error_name in ERROR_MESSAGES.items():
            is_active = bool(error_flags & (1 << bit_pos))
            attrs[f"bit_{bit_pos}_{error_name.lower().replace('-', '_')}"] = is_active

        return attrs

    @property
    def device_info(self) -> dict:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.inverter_id or self.coordinator.config_entry.entry_id)},
            "name": f"Eversolar Inverter {self.coordinator.inverter_id or 'Unknown'}",
            "manufacturer": "Eversolar",
            "model": "PMU (TCP/IP)",
        }


class EversolarDailyEfficiencySensor(CoordinatorEntity, SensorEntity):
    """Daily Efficiency sensor."""

    _attr_has_entity_name = True
    _attr_name = "Daily Efficiency"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: EversolarDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_daily_efficiency"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_daily_efficiency"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False
        # Available only if both energy and power data exist
        if not self.coordinator.data:
            return False
        energy = self.coordinator.data.get("e_today_kwh")
        power = self.coordinator.data.get("pv_w_est")
        return energy is not None and power is not None and power > 0

    @property
    def native_value(self) -> Optional[float]:
        """Return the daily efficiency percentage."""
        if not self.coordinator.data:
            return None

        energy_kwh = self.coordinator.data.get("e_today_kwh")
        power_w = self.coordinator.data.get("pv_w_est")

        if energy_kwh is None or power_w is None or power_w <= 0:
            return None

        # efficiency = (energy_kwh / 24 / (power_w / 1000)) * 100
        try:
            efficiency = (energy_kwh / 24 / (power_w / 1000)) * 100
            return round(efficiency, 1)
        except (ValueError, ZeroDivisionError):
            return None

    @property
    def device_info(self) -> dict:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.inverter_id or self.coordinator.config_entry.entry_id)},
            "name": f"Eversolar Inverter {self.coordinator.inverter_id or 'Unknown'}",
            "manufacturer": "Eversolar",
            "model": "PMU (TCP/IP)",
        }
