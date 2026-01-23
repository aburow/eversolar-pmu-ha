"""Sensor platform for Eversolar PMU."""
import logging
from typing import Any, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
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
    DOMAIN,
    SENSOR_DATA_KEYS,
    SENSOR_ENERGY_TODAY,
    SENSOR_ENERGY_TOTAL,
    SENSOR_FREQUENCY,
    SENSOR_HOURS_TOTAL,
    SENSOR_POWER,
    SENSOR_PV_CURRENT,
    SENSOR_PV_POWER,
    SENSOR_PV_VOLTAGE,
    SENSOR_TIME_DELTA,
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
        EversolarDiagnosticSensor(
            coordinator,
            SENSOR_TIME_DELTA,
            "PMU Time Delta",
            "time_delta",
            None,
            "s",
            SensorStateClass.MEASUREMENT,
        ),
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
            "model": "PMU",
            "sw_version": "1.0",
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
