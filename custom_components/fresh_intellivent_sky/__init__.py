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

from .const import (
    AIRING_MODE_UPDATE,
    CONF_AUTH_KEY,
    CONSTANT_SPEED_UPDATE,
    DEFAULT_SCAN_INTERVAL,
    DELAY_KEY,
    DETECTION_KEY,
    DOMAIN,
    ENABLED_KEY,
    HUMIDITY_MODE_UPDATE,
    LIGHT_AND_VOC_MODE_UPDATE,
    MINUTES_KEY,
    RPM_KEY,
    TIMER_MODE_UPDATE,
)


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

    async def _async_update_method():  # pylint: disable=too-many-branches, too-many-statements
        """Get data from Fresh Intellivent Sky."""
        ble_device = bluetooth.async_ble_device_from_address(hass, address)
        fresh = FreshIntelliVent()

        try:
            async with fresh.connect(ble_device) as client:
                if auth_key is not None:
                    await client.authenticate(authentication_code=auth_key)
                await client.fetch_sensor_data()
                await client.fetch_device_information()

                if auth_key is not None:
                    await client.fetch_airing()
                    await client.fetch_constant_speed()
                    await client.fetch_humidity()
                    await client.fetch_light_and_voc()
                    await client.fetch_timer()
                else:
                    return fresh

                updated = False

                try:
                    humidity_mode = hass.data[HUMIDITY_MODE_UPDATE]

                    if humidity_mode is not None:
                        await client.update_humidity(
                            enabled=bool(humidity_mode[ENABLED_KEY]),
                            detection=humidity_mode[DETECTION_KEY],
                            rpm=int(humidity_mode[RPM_KEY]),
                        )
                        updated = True
                        _LOGGER.debug("Updated humidity mode")

                except Exception as err:  # pylint: disable=broad-except
                    _LOGGER.warning("Failed to update humidity: %s", err)
                finally:
                    hass.data[HUMIDITY_MODE_UPDATE] = None

                try:
                    light_and_voc_mode = hass.data[LIGHT_AND_VOC_MODE_UPDATE]

                    if light_and_voc_mode is not None:
                        light = light_and_voc_mode["light"]
                        voc = light_and_voc_mode["voc"]

                        await client.update_light_and_voc(
                            light_enabled=bool(light[ENABLED_KEY]),
                            light_detection=light[DETECTION_KEY],
                            voc_enabled=bool(voc[ENABLED_KEY]),
                            voc_detection=voc[DETECTION_KEY],
                        )
                        updated = True
                        _LOGGER.debug("Updated light and voc mode")
                except Exception as err:  # pylint: disable=broad-except
                    _LOGGER.warning("Failed to update light and voc mode: %s", err)
                finally:
                    hass.data[LIGHT_AND_VOC_MODE_UPDATE] = None

                try:
                    airing_mode = hass.data[AIRING_MODE_UPDATE]

                    if airing_mode is not None:
                        await client.update_airing(
                            enabled=bool(airing_mode[ENABLED_KEY]),
                            minutes=airing_mode[MINUTES_KEY],
                            rpm=airing_mode[RPM_KEY],
                        )
                        updated = True
                        _LOGGER.debug("Updated airing mode")
                except Exception as err:  # pylint: disable=broad-except
                    _LOGGER.warning("Failed to update airing mode: %s", err)
                finally:
                    hass.data[AIRING_MODE_UPDATE] = None

                try:
                    constant_speed = hass.data[CONSTANT_SPEED_UPDATE]

                    if constant_speed is not None:
                        await client.update_constant_speed(
                            enabled=constant_speed[ENABLED_KEY],
                            rpm=constant_speed[RPM_KEY],
                        )
                        updated = True
                        _LOGGER.debug("Updated constant speed")
                except Exception as err:  # pylint: disable=broad-except
                    _LOGGER.warning("Failed to update constant speed: %s", err)
                finally:
                    hass.data[CONSTANT_SPEED_UPDATE] = None

                try:
                    timer_mode = hass.data[TIMER_MODE_UPDATE]

                    if timer_mode is not None:
                        await client.update_timer(
                            minutes=timer_mode[MINUTES_KEY],
                            delay_enabled=timer_mode[DELAY_KEY][ENABLED_KEY],
                            delay_minutes=timer_mode[DELAY_KEY][MINUTES_KEY],
                            rpm=timer_mode[RPM_KEY],
                        )
                        updated = True
                        _LOGGER.debug("Updated timer mode")
                except Exception as err:  # pylint: disable=broad-except
                    _LOGGER.warning("Failed to update timer mode: %s", err)
                finally:
                    hass.data[TIMER_MODE_UPDATE] = None

                if updated:
                    await client.fetch_sensor_data()

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.warning("Failed to fetch data: %s", err)
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
