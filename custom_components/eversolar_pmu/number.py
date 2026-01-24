"""Number platform for Eversolar PMU."""
import logging
from typing import Any, Optional

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_PV_VOLTAGE_STATS_CUTOFF, DOMAIN
from .coordinator import EversolarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number platform from a config entry."""
    coordinator: EversolarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EversolarPVVoltageStatsCutoffNumber(coordinator),
    ]

    async_add_entities(entities)


class EversolarPVVoltageStatsCutoffNumber(CoordinatorEntity, NumberEntity):
    """PV Voltage Stats Cutoff number entity."""

    _attr_has_entity_name = True
    _attr_name = "PV Voltage Stats Cutoff"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 200
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "V"

    def __init__(self, coordinator: EversolarDataUpdateCoordinator) -> None:
        """Initialize number entity."""
        super().__init__(coordinator)
        self.coordinator = coordinator

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_pv_voltage_stats_cutoff"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_pv_voltage_stats_cutoff"

    @property
    def native_value(self) -> Optional[float]:
        """Return the current PV voltage stats cutoff."""
        return float(self.coordinator._get_config(CONF_PV_VOLTAGE_STATS_CUTOFF, 20))

    async def async_set_native_value(self, value: float) -> None:
        """Set PV voltage stats cutoff."""
        self.coordinator.config_entry.options[CONF_PV_VOLTAGE_STATS_CUTOFF] = int(value)
        self.async_write_ha_state()
        # Trigger coordinator update to refresh available states
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> dict:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.inverter_id or self.coordinator.config_entry.entry_id)},
            "name": f"Eversolar Inverter {self.coordinator.inverter_id or 'Unknown'}",
            "manufacturer": "Eversolar",
            "model": "PMU",
            "sw_version": "1.1.2",
        }
