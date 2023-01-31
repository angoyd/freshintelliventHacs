"""Support for numbers."""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import REVOLUTIONS_PER_MINUTE, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pyfreshintellivent import FreshIntelliVent

from .const import (
    AIRING_MODE_UPDATE,
    CONSTANT_SPEED_UPDATE,
    DELAY_KEY,
    DETECTION_KEY,
    DOMAIN,
    ENABLED_KEY,
    HUMIDITY_MODE_UPDATE,
    MINUTES_KEY,
    RPM_KEY,
    TIMER_MODE_UPDATE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors dynamically through discovery."""
    coordinator: DataUpdateCoordinator[FreshIntelliVent] = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    async_add_entities(
        [
            FreshIntelliventSkyNumber(
                coordinator,
                coordinator.data,
                NumberEntityDescription(
                    key="humidity_and_voc_rpm",
                    name="Humidity and VOC",
                    native_min_value=800,
                    native_max_value=2400,
                    native_step=1,
                    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                ),
                entity_category=EntityCategory.CONFIG,
                keys=["humidity", "rpm"],
            ),
            FreshIntelliventSkyNumber(
                coordinator,
                coordinator.data,
                NumberEntityDescription(
                    key="constant_speed_rpm",
                    name="Constant speed",
                    native_min_value=800,
                    native_max_value=2400,
                    native_step=1,
                    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                ),
                entity_category=EntityCategory.CONFIG,
                keys=["constant_speed", "rpm"],
            ),
            FreshIntelliventSkyNumber(
                coordinator,
                coordinator.data,
                NumberEntityDescription(
                    key="airing_rpm",
                    name="Airing",
                    native_min_value=800,
                    native_max_value=2400,
                    native_step=1,
                    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                ),
                entity_category=EntityCategory.CONFIG,
                keys=["airing", "rpm"],
            ),
            FreshIntelliventSkyNumber(
                coordinator,
                coordinator.data,
                NumberEntityDescription(
                    key="airing_minutes",
                    name="Airing minutes",
                    native_min_value=5,
                    native_max_value=120,
                    native_step=1,
                    native_unit_of_measurement=UnitOfTime.MINUTES,
                ),
                entity_category=EntityCategory.CONFIG,
                keys=["airing", "minutes"],
            ),
            FreshIntelliventSkyNumber(
                coordinator,
                coordinator.data,
                NumberEntityDescription(
                    key="timer_and_light_rpm",
                    name="Timer and light",
                    native_min_value=800,
                    native_max_value=2400,
                    native_step=1,
                    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                ),
                entity_category=EntityCategory.CONFIG,
                keys=["timer", "rpm"],
            ),
            FreshIntelliventSkyNumber(
                coordinator,
                coordinator.data,
                NumberEntityDescription(
                    key="timer_minutes",
                    name="Timer minutes",
                    native_min_value=1,
                    native_max_value=60,
                    native_step=1,
                    native_unit_of_measurement=UnitOfTime.MINUTES,
                ),
                entity_category=EntityCategory.CONFIG,
                keys=["timer", "minutes"],
            ),
            FreshIntelliventSkyNumber(
                coordinator,
                coordinator.data,
                NumberEntityDescription(
                    key="timer_delay_minutes",
                    name="Timer delay minutes",
                    native_min_value=0,
                    native_max_value=10,
                    native_step=1,
                    native_unit_of_measurement=UnitOfTime.MINUTES,
                ),
                entity_category=EntityCategory.CONFIG,
                keys=["timer", "delay", "minutes"],
            ),
        ]
    )


class FreshIntelliventSkyNumber(
    CoordinatorEntity[DataUpdateCoordinator[FreshIntelliVent]], NumberEntity
):
    """Fresh Intellivent Sky numbers for the device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: FreshIntelliVent,
        entity_description: NumberEntityDescription,
        entity_category: EntityCategory | None = None,
        keys: list | None = None,
    ) -> None:
        """Populate the airthings entity with relevant data."""
        super().__init__(coordinator)
        self.entity_description = entity_description

        name = f"{device.manufacturer} {device.name}"

        self.device = device
        self._attr_unique_id = f"{device.manufacturer}_{name}_{entity_description.key}"
        self._attr_entity_category = entity_category
        self._keys = keys
        self._id = device.address
        self._attr_device_info = DeviceInfo(
            connections={
                (
                    CONNECTION_BLUETOOTH,
                    device.address,
                )
            },
            name=name,
            manufacturer=device.manufacturer,
            model=device.model,
            hw_version=device.hw_version,
            sw_version=device.fw_version,
        )

    @property
    def native_value(self) -> float | None:
        """Return the reported value."""
        if self._keys is None:
            return None
        value = self.coordinator.data.modes
        for key in self._keys:
            if value.get(key) is None:
                return None
            value = value[key]

        return value

    async def async_set_native_value(self, value: float) -> None:
        """Set value."""
        key = self.entity_description.key

        if key == "humidity_and_voc_rpm":
            self.coordinator.hass.data[HUMIDITY_MODE_UPDATE] = {
                ENABLED_KEY: self.device.modes["humidity"][ENABLED_KEY],
                DETECTION_KEY: self.device.modes["humidity"][DETECTION_KEY],
                RPM_KEY: int(value),
            }
        elif key == "constant_speed_rpm":
            self.coordinator.hass.data[CONSTANT_SPEED_UPDATE] = {
                ENABLED_KEY: self.device.modes["constant_speed"][ENABLED_KEY],
                RPM_KEY: int(value),
            }
        elif key == "airing_rpm":
            self.coordinator.hass.data[AIRING_MODE_UPDATE] = {
                ENABLED_KEY: self.device.modes["airing"][ENABLED_KEY],
                MINUTES_KEY: self.device.modes["airing"][MINUTES_KEY],
                RPM_KEY: int(value),
            }
        elif key == "airing_rpm":
            self.coordinator.hass.data[AIRING_MODE_UPDATE] = {
                ENABLED_KEY: self.device.modes["airing"][ENABLED_KEY],
                MINUTES_KEY: self.device.modes["airing"][MINUTES_KEY],
                RPM_KEY: int(value),
            }
        elif key == "airing_minutes":
            self.coordinator.hass.data[AIRING_MODE_UPDATE] = {
                ENABLED_KEY: self.device.modes["airing"][ENABLED_KEY],
                MINUTES_KEY: int(value),
                RPM_KEY: self.device.modes["airing"][RPM_KEY],
            }
        elif key == "timer_and_light_rpm":
            self.coordinator.hass.data[TIMER_MODE_UPDATE] = {
                MINUTES_KEY: self.device.modes["timer"][MINUTES_KEY],
                DELAY_KEY: {
                    ENABLED_KEY: self.device.modes["timer"][DELAY_KEY][ENABLED_KEY],
                    MINUTES_KEY: self.device.modes["timer"][DELAY_KEY][MINUTES_KEY],
                },
                RPM_KEY: int(value),
            }
        elif key == "timer_minutes":
            self.coordinator.hass.data[TIMER_MODE_UPDATE] = {
                MINUTES_KEY: int(value),
                DELAY_KEY: {
                    ENABLED_KEY: self.device.modes["timer"][DELAY_KEY][ENABLED_KEY],
                    MINUTES_KEY: self.device.modes["timer"][DELAY_KEY][MINUTES_KEY],
                },
                RPM_KEY: self.device.modes["timer"][RPM_KEY],
            }
        elif key == "timer_delay_minutes":
            delay_minutes = int(value)
            delay_enabled = delay_minutes > 0

            self.coordinator.hass.data[TIMER_MODE_UPDATE] = {
                MINUTES_KEY: self.device.modes["timer"][MINUTES_KEY],
                DELAY_KEY: {
                    ENABLED_KEY: delay_enabled,
                    MINUTES_KEY: delay_minutes,
                },
                RPM_KEY: self.device.modes["timer"][RPM_KEY],
            }

        await self.coordinator.async_request_refresh()
