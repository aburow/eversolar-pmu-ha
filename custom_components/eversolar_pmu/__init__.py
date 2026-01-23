"""Eversolar PMU integration."""
import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback

from .const import CONF_HOST, DOMAIN
from .coordinator import EversolarDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Eversolar PMU component."""
    hass.data.setdefault(DOMAIN, {})

    # Support YAML configuration (legacy)
    if DOMAIN in config:
        for conf in config[DOMAIN]:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": "import"},
                    data=conf,
                )
            )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eversolar PMU from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = EversolarDataUpdateCoordinator(hass, entry)

    # Perform initial data fetch
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    @callback
    async def handle_sync_time(call: ServiceCall) -> None:
        """Handle sync_time service call."""
        config_entry_id = call.data.get("config_entry_id")

        if config_entry_id and config_entry_id in hass.data[DOMAIN]:
            coord = hass.data[DOMAIN][config_entry_id]
            success = await coord.async_sync_time()
            if not success:
                _LOGGER.error("Failed to sync PMU time for config entry %s", config_entry_id)
        else:
            _LOGGER.error("Config entry %s not found", config_entry_id)

    hass.services.async_register(
        DOMAIN,
        "sync_time",
        handle_sync_time,
        schema=vol.Schema(
            {
                vol.Required("config_entry_id"): str,
            }
        ),
    )

    # Update entry options listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

        # If no more entries, remove domain data and unregister services
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "sync_time")

    return unload_ok
