"""Config flow for Eversolar PMU integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.config_validation import All, Range
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    CONF_AUTO_SYNC_DELAY,
    CONF_AUTO_SYNC_ENABLED,
    CONF_HOST,
    CONF_PORT,
    CONF_PV_VOLTAGE_THRESHOLD,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    CONF_TIMEZONE,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_TIMEZONE,
    DOMAIN,
)
from .eversolar_protocol import EversolarPMU

_LOGGER = logging.getLogger(__name__)

# Common timezones
TIMEZONES = [
    "Australia/Brisbane",
    "Australia/Sydney",
    "Australia/Melbourne",
    "Australia/Perth",
    "Australia/Adelaide",
    "Australia/Darwin",
    "UTC",
    "America/New_York",
    "America/Los_Angeles",
    "Europe/London",
    "Europe/Berlin",
    "Asia/Tokyo",
    "Asia/Shanghai",
    "Asia/Singapore",
]


class EversolarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eversolar PMU."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]

            # Validate connection
            try:
                is_reachable = await self.hass.async_add_executor_job(
                    EversolarPMU.test_connection,
                    host,
                    user_input.get(CONF_PORT, DEFAULT_PORT),
                    user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                )
                if not is_reachable:
                    errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Error testing connection: %s", err)
                errors["base"] = "cannot_connect"

            if not errors:
                # Create unique ID based on host
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Eversolar PMU ({host})",
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=300)
                ),
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
                    vol.Coerce(float), vol.Range(min=1.0, max=30.0)
                ),
                vol.Optional(CONF_TIMEZONE, default=DEFAULT_TIMEZONE): SelectSelector(
                    SelectSelectorConfig(options=TIMEZONES)
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "EversolarOptionsFlow":
        """Get the options flow for this config entry."""
        return EversolarOptionsFlow(config_entry)


class EversolarOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Eversolar PMU."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.data.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
                vol.Optional(
                    CONF_TIMEOUT,
                    default=self.config_entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
                ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=30.0)),
                vol.Optional(
                    CONF_TIMEZONE,
                    default=self.config_entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE),
                ): SelectSelector(SelectSelectorConfig(options=TIMEZONES)),
                vol.Optional(
                    CONF_AUTO_SYNC_ENABLED,
                    default=self.config_entry.data.get(CONF_AUTO_SYNC_ENABLED, False),
                ): bool,
                vol.Optional(
                    CONF_AUTO_SYNC_DELAY,
                    default=self.config_entry.data.get(CONF_AUTO_SYNC_DELAY, 1),
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Optional(
                    CONF_PV_VOLTAGE_THRESHOLD,
                    default=self.config_entry.data.get(CONF_PV_VOLTAGE_THRESHOLD, 50),
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=200)),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
