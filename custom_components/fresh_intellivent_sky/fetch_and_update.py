from homeassistant.core import HomeAssistant
from pyfreshintellivent import FreshIntelliVent
import logging
from .const import (
    AIRING_MODE_UPDATE,
    BOOST_UPDATE,
    CONSTANT_SPEED_UPDATE,
    DELAY_KEY,
    DETECTION_KEY,
    ENABLED_KEY,
    HUMIDITY_MODE_UPDATE,
    LIGHT_AND_VOC_MODE_UPDATE,
    MINUTES_KEY,
    RPM_KEY,
    PAUSE_UPDATE,
    TIMER_MODE_UPDATE,
)

UPDATE_NEEDED = "update_needed"
UPDATE_DONE = "update_done"

_LOGGER = logging.getLogger(__name__)


class FetchAndUpdate:
    def __init__(self, hass: HomeAssistant, client: FreshIntelliVent):
        self._hass = hass
        self._client = client

        self._is_authenticated = client.sensors.authenticated
    
    async def update_all(self):
        self._update_boost()
        self._update_pause()
        self._fetch_and_update_airing()
        self._fetch_and_update_constant_speed()
        self._fetch_and_update_humidity()
        self._fetch_and_update_light_and_voc()
        self._fetch_and_update_timer()

    async def _update_boost(self):
        boost = self._hass.data[BOOST_UPDATE]

        if boost is not None and self._is_authenticated is True:
            await self._client.update_boost(
                enabled=boost[ENABLED_KEY],
                rpm=boost[RPM_KEY],
                seconds=boost[MINUTES_KEY]
            )
            _LOGGER.debug("Updated constant speed")
            self._hass.data[BOOST_UPDATE] = None

    async def _update_pause(self):
        pause = self._hass.data[PAUSE_UPDATE]

        if pause is not None and self._is_authenticated is True:
            await self._client.update_pause(
                enabled=bool(pause[ENABLED_KEY]),
                seconds=int(pause[MINUTES_KEY]),
            )
            _LOGGER.debug("Updated pause: %s", pause)
            self._hass.data[PAUSE_UPDATE] = None

    async def _fetch_and_update_airing(self):
        airing_mode = self._hass.data[AIRING_MODE_UPDATE]

        if airing_mode is not None and self._is_authenticated is True:
            await self._client.update_airing(
                enabled=bool(airing_mode[ENABLED_KEY]),
                minutes=int(airing_mode[MINUTES_KEY]),
                rpm=int(airing_mode[RPM_KEY]),
            )
            _LOGGER.debug("Updated airing mode: %s", airing_mode)
            self._hass.data[AIRING_MODE_UPDATE] = None
        else:
            await self._client.fetch_airing()

    async def _fetch_and_update_constant_speed(self):
        constant_speed = self._hass.data[CONSTANT_SPEED_UPDATE]

        if constant_speed is not None and self._is_authenticated is True:
            await self._client.update_constant_speed(
                enabled=constant_speed[ENABLED_KEY],
                rpm=constant_speed[RPM_KEY],
            )
            _LOGGER.debug("Updated constant speed: %s", constant_speed)
            self._hass.data[CONSTANT_SPEED_UPDATE] = None
        else:
            await self._client.fetch_constant_speed()

    async def _fetch_and_update_humidity(self):
        humidity_mode = self._hass.data[HUMIDITY_MODE_UPDATE]

        if humidity_mode is not None and self._is_authenticated is True:
            await self._client.update_humidity(
                enabled=bool(humidity_mode[ENABLED_KEY]),
                detection=humidity_mode[DETECTION_KEY],
                rpm=int(humidity_mode[RPM_KEY]),
            )
            _LOGGER.debug("Updated humidity mode: %s", humidity_mode)
            self._hass.data[HUMIDITY_MODE_UPDATE] = None
        else:
            await self._client.fetch_humidity()

    async def _fetch_and_update_light_and_voc(self):
        light_and_voc_mode = self._hass.data[LIGHT_AND_VOC_MODE_UPDATE]

        if light_and_voc_mode is not None and self._is_authenticated is True:
            light = light_and_voc_mode["light"]
            voc = light_and_voc_mode["voc"]

            await self._client.update_light_and_voc(
                light_enabled=bool(light[ENABLED_KEY]),
                light_detection=light[DETECTION_KEY],
                voc_enabled=bool(voc[ENABLED_KEY]),
                voc_detection=voc[DETECTION_KEY],
            )
            _LOGGER.debug("Updated light and voc mode: %s", light_and_voc_mode)
            self._hass.data[LIGHT_AND_VOC_MODE_UPDATE] = None
        else:
            await self._client.fetch_light_and_voc()

    async def _fetch_and_update_timer(self):
        timer_mode = self._hass.data[TIMER_MODE_UPDATE]

        if timer_mode is not None and self._is_authenticated is True:
            await self._client.update_timer(
                minutes=timer_mode[MINUTES_KEY],
                delay_enabled=timer_mode[DELAY_KEY][ENABLED_KEY],
                delay_minutes=timer_mode[DELAY_KEY][MINUTES_KEY],
                rpm=timer_mode[RPM_KEY],
            )
            _LOGGER.debug("Updated timer mode: %s", timer_mode)
            self._hass.data[TIMER_MODE_UPDATE] = None
        else:
            await self._client.fetch_timer()
