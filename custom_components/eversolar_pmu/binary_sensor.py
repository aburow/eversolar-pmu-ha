# SPDX-License-Identifier: GPL-3.0
# Copyright (C) 2026 Anthony Burow
# https://github.com/aburow/eversolar-pmu-ha

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
        EversolarACDCOfflineSensor(coordinator),
        EversolarTimeSyncSensor(coordinator),
    ]

    async_add_entities(entities)


class EversolarACDCOfflineSensor(CoordinatorEntity, BinarySensorEntity):
    """DC Online binary sensor."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: EversolarDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_name = "DC Online"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_dc_online"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_dc_online"

    @property
    def is_on(self) -> Optional[bool]:
        """Return True if DC is online (inverter not fully down)."""
        if self.coordinator.is_fully_down is not None:
            return not self.coordinator.is_fully_down
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


class EversolarTimeSyncSensor(CoordinatorEntity, BinarySensorEntity):
    """Time Sync binary sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: EversolarDataUpdateCoordinator) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self._attr_name = "Time Sync"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self.coordinator.inverter_id:
            return f"{DOMAIN}_{self.coordinator.inverter_id}_time_sync"
        return f"{DOMAIN}_{self.coordinator.config_entry.entry_id}_time_sync"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not super().available:
            return False
        # Unavailable when both AC and DC are down (fully down)
        if self.coordinator.is_fully_down:
            return False
        return True

    @property
    def is_on(self) -> bool:
        """Return True if time sync was successful."""
        return self.coordinator.time_sync_success

    @property
    def device_info(self) -> dict:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.coordinator.inverter_id or self.coordinator.config_entry.entry_id)},
            "name": f"Eversolar Inverter {self.coordinator.inverter_id or 'Unknown'}",
            "manufacturer": "Eversolar",
            "model": "PMU (TCP/IP)",
        }
