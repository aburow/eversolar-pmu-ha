"""Data update coordinator for Eversolar PMU."""
import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, CONF_TIMEOUT, CONF_TIMEZONE, DEFAULT_SCAN_INTERVAL, DEFAULT_TIMEOUT, DEFAULT_TIMEZONE, DOMAIN
from .eversolar_protocol import EversolarPMU

_LOGGER = logging.getLogger(__name__)


class EversolarDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate Eversolar PMU data updates."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialize coordinator."""
        self.pmu = EversolarPMU(
            host=entry.data[CONF_HOST],
            port=entry.data.get(CONF_PORT, 8080),
            timeout=entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        )
        self.config_entry = entry
        self.inverter_id = None

        update_interval = timedelta(
            seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from PMU."""
        try:
            data = await self.hass.async_add_executor_job(
                self.pmu.connect_and_poll,
                False,  # set_time=False for normal polling
                self.config_entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE),
            )

            # Store inverter ID on first successful poll
            if self.inverter_id is None:
                self.inverter_id = data.get("inverter_id")
                _LOGGER.debug("Inverter ID: %s", self.inverter_id)

            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with PMU: {err}") from err

    async def async_sync_time(self) -> bool:
        """Sync PMU time to host time."""
        try:
            tz_name = self.config_entry.data.get(CONF_TIMEZONE, DEFAULT_TIMEZONE)
            await self.hass.async_add_executor_job(
                self.pmu.sync_time,
                tz_name,
            )
            _LOGGER.debug("PMU time synced")
            # Request immediate refresh to update time_delta
            await self.async_request_refresh()
            return True
        except Exception as err:
            _LOGGER.error("Error syncing PMU time: %s", err)
            return False
