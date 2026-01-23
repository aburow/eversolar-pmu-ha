"""Binary sensor platform for Eversolar PMU."""
import logging
from typing import Optional

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_PV_VOLTAGE_THRESHOLD, DOMAIN
from .coordinator import EversolarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor platform from a config entry."""
    coordinator: EversolarDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        EversolarACOnlineSensor(coordinator),
        EversolarFullyDownSensor(coordinator),
    ]

    async_add_entities(entities)


class EversolarACOnlineSensor(CoordinatorEntity, BinarySensorEntity):
    """AC Online binary sensor."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: EversolarDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_name = "AC Online"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_ac_online"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_ac_online"

    @property
    def is_on(self) -> Optional[bool]:
        """Return True if AC is online (Normal mode)."""
        if not self.coordinator.data:
            return None
        mode = self.coordinator.data.get("mode")
        return mode == 0x0001

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


class EversolarFullyDownSensor(CoordinatorEntity, BinarySensorEntity):
    """Fully Down binary sensor."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: EversolarDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_name = "Fully Down"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_fully_down"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_fully_down"

    @property
    def is_on(self) -> Optional[bool]:
        """Return True if inverter is fully down."""
        return self.coordinator.is_fully_down if self.coordinator.is_fully_down is not None else None

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
