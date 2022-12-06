"""The Fresh Intellivent Sky integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers.update_coordinator import (DataUpdateCoordinator,
                                                      UpdateFailed)
from pyfreshintellivent import FreshIntelliVent

from .const import (AIRING_MODE_UPDATE, CONF_AUTH_KEY, CONSTANT_SPEED_UPDATE,
                    DEFAULT_SCAN_INTERVAL, DOMAIN, HUMIDITY_MODE_UPDATE,
                    LIGHT_AND_VOC_MODE_UPDATE, TIMER_MODE_UPDATE)
from .fetch_and_update import FetchAndUpdate


class UnableToConnect(HomeAssistantError):
    """Exception to indicate that we can not connect to device."""


ALL_UPDATES = [
    CONSTANT_SPEED_UPDATE,
    AIRING_MODE_UPDATE,
    HUMIDITY_MODE_UPDATE,
    LIGHT_AND_VOC_MODE_UPDATE,
    TIMER_MODE_UPDATE,
]

AUTHENTICATED_PLATFORMS = [
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

READ_ONLY_PLATFORMS = [
    Platform.SENSOR,
]

MAX_ATTEMPTS = 5
TIMEOUT = 30.0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:  # pyling: disable=too-many-statements
    """Set up Fresh Intellivent Sky."""
    hass.data.setdefault(DOMAIN, {})
    address = entry.unique_id

    assert address is not None

    # Make sure we remove all old data
    for update in ALL_UPDATES:
        hass.data[update] = None

    ble_device = bluetooth.async_ble_device_from_address(hass, address)
    auth_key = entry.data.get(CONF_AUTH_KEY)

    if not ble_device:
        raise ConfigEntryNotReady(
            f"Could not find Fresh Intellivent Sky device with address {address}"
        )

    async def _async_update_method():
        """Get data from Fresh Intellivent Sky."""
        ble_device = bluetooth.async_ble_device_from_address(hass, address)
        fresh = FreshIntelliVent()

        attempts = 0
        while attempts < MAX_ATTEMPTS:
            try:
                async with fresh.connect(ble_device, TIMEOUT) as client:
                    if auth_key is not None:
                        await client.authenticate(authentication_code=auth_key)
                    await client.fetch_sensor_data()
                    await client.fetch_device_information()

                    updates = FetchAndUpdate(hass=hass, client=client)
                    await updates.update_all()

            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.warning("Failed to fetch data: %s", err)
                if attempts > MAX_ATTEMPTS:
                    raise UpdateFailed(f"Unable to fetch data: {err}") from err
                attempts += 1
                _LOGGER.warning("Retry, attempt number %s / %s", attempts, MAX_ATTEMPTS)

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

    if auth_key is not None:
        platforms = AUTHENTICATED_PLATFORMS
    else:
        platforms = READ_ONLY_PLATFORMS

    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, AUTHENTICATED_PLATFORMS
    ):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
