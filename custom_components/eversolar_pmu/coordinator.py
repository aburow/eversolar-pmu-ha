"""Data update coordinator for Eversolar PMU."""
import logging
from datetime import date, datetime, timedelta, timezone

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_AUTO_SYNC_DELAY,
    CONF_AUTO_SYNC_ENABLED,
    CONF_HOST,
    CONF_PORT,
    CONF_PV_VOLTAGE_THRESHOLD,
    CONF_SCAN_INTERVAL,
    CONF_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DOMAIN,
)
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

        # State tracking variables
        self._last_mode: int | None = None
        self._sync_pending: bool = False
        self._sync_trigger_time: datetime | None = None
        self._synced_today: bool = False
        self._last_sync_date: date | None = None
        self._is_fully_down: bool = False
        self._ac_online_time: datetime | None = None
        self._ac_offline_time: datetime | None = None

        update_interval = timedelta(
            seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    def _get_config(self, key: str, default=None):
        """Get config value from options first, then data, then default."""
        return self.config_entry.options.get(key) or self.config_entry.data.get(key, default)

    @property
    def is_fully_down(self) -> bool:
        """Check if inverter is fully down (Wait mode + low PV voltage)."""
        if not self.data:
            return False
        mode = self.data.get("mode")
        pv_voltage = self.data.get("pv_v", 0) or 0
        threshold = self._get_config(CONF_PV_VOLTAGE_THRESHOLD, 50)
        return mode == 0x0000 and pv_voltage < threshold

    async def _async_update_data(self) -> dict:
        """Fetch data from PMU."""
        try:
            data = await self.hass.async_add_executor_job(
                self.pmu.connect_and_poll,
                False,  # set_time=False for normal polling
                self.hass.config.time_zone,
            )

            # Store inverter ID on first successful poll
            if self.inverter_id is None:
                self.inverter_id = data.get("inverter_id")
                _LOGGER.debug("Inverter ID: %s", self.inverter_id)

            # Check if auto-sync feature is enabled
            auto_sync_enabled = self._get_config(CONF_AUTO_SYNC_ENABLED, False)
            if auto_sync_enabled:
                current_mode = data.get("mode")
                pv_voltage = data.get("pv_v")
                current_date = datetime.now().date()

                # Reset daily sync flag at midnight
                if self._last_sync_date != current_date:
                    self._synced_today = False
                    self._last_sync_date = current_date

                # Detect transition from Wait (0x0000) to Normal (0x0001)
                if (
                    not self._synced_today
                    and not self._sync_pending
                    and self._last_mode == 0x0000
                    and current_mode == 0x0001
                ):
                    # Inverter just started up - voltage exceeded threshold
                    delay_minutes = self._get_config(CONF_AUTO_SYNC_DELAY, 1)
                    delay_seconds = delay_minutes * 60
                    self._sync_trigger_time = datetime.now() + timedelta(seconds=delay_seconds)
                    self._sync_pending = True
                    _LOGGER.info(
                        "Inverter startup detected (Wait → Normal, PV voltage: %sV). "
                        "Time sync scheduled in %d minute(s)",
                        pv_voltage if pv_voltage else "unknown",
                        delay_minutes,
                    )

                # Execute sync if trigger time reached
                if (
                    self._sync_pending
                    and self._sync_trigger_time
                    and datetime.now() >= self._sync_trigger_time
                ):
                    _LOGGER.info("Executing automatic time sync")
                    success = await self.async_sync_time()
                    if success:
                        self._synced_today = True
                        self._sync_pending = False
                        self._sync_trigger_time = None
                        _LOGGER.info("Automatic time sync completed successfully")
                    else:
                        _LOGGER.warning("Automatic time sync failed, will retry next poll")

                # Update last mode for next comparison
                self._last_mode = current_mode

            # Track AC online/offline transitions
            current_mode = data.get("mode")
            if current_mode is not None and self._last_mode is not None:
                if self._last_mode == 0x0000 and current_mode == 0x0001:
                    # Wait → Normal: AC came online
                    self._ac_online_time = datetime.now(timezone.utc)
                    data["ac_online_time"] = self._ac_online_time.isoformat()
                    _LOGGER.info("AC came online at %s", self._ac_online_time.isoformat())
                elif self._last_mode == 0x0001 and current_mode == 0x0000:
                    # Normal → Wait: AC went offline
                    self._ac_offline_time = datetime.now(timezone.utc)
                    data["ac_offline_time"] = self._ac_offline_time.isoformat()
                    _LOGGER.info("AC went offline at %s", self._ac_offline_time.isoformat())

            # Add timestamps to data if available
            if self._ac_online_time:
                data["ac_online_time"] = self._ac_online_time.isoformat()
            if self._ac_offline_time:
                data["ac_offline_time"] = self._ac_offline_time.isoformat()

            # Update fully_down state tracking
            self._is_fully_down = self.is_fully_down

            return data
        except Exception as err:
            raise UpdateFailed(f"Error communicating with PMU: {err}") from err

    async def async_sync_time(self) -> bool:
        """Sync PMU time to host time."""
        try:
            tz_name = self.hass.config.time_zone
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
