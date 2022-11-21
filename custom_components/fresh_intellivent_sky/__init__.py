"""The Fresh Intellivent Sky integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from pyfreshintellivent import FreshIntelliVent

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN


class UnableToConnect(HomeAssistantError):
    """Exception to indicate that we can not connect to device."""


PLATFORMS = [
    # Platform.FAN,
    Platform.SENSOR,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fresh Intellivent Sky."""
    hass.data.setdefault(DOMAIN, {})
    address = entry.unique_id
    auth_code = "CHANGEME"

    assert address is not None
    assert auth_code is not None

    ble_device = bluetooth.async_ble_device_from_address(hass, address)

    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find Fresh Intellivent Sky device with address {address}"
        )

    async def _async_update_method():
        """Get data from Fresh Intellivent Sky."""
        ble_device = bluetooth.async_ble_device_from_address(hass, address)
        fresh = FreshIntelliVent()

        try:
            async with fresh.connect(ble_device) as client:
                await client.authenticate(auth_code)
                await client.fetch_sensor_data()
                if client.sensors.authenticated is False:
                    raise UpdateFailed("Not authenticated. Wrong authentication code?")
                await client.fetch_device_information()
                await client.fetch_airing()
                await client.fetch_constant_speed()
                await client.fetch_humidity()
                await client.fetch_light_and_voc()
                await client.fetch_timer()

        except Exception as err:
            raise UpdateFailed(f"Unable to fetch data: {err}") from err

        return fresh

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=_async_update_method,
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
