"""Support for switches."""
from __future__ import annotations

import logging
from typing import cast

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pyfreshintellivent import FreshIntelliVent

from .const import CONSTANT_SPEED_UPDATE, DOMAIN, ENABLED_KEY, RPM_KEY

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
            FreshIntelliventSkySwitch(
                coordinator,
                coordinator.data,
                SwitchEntityDescription(
                    key="constant_speed_enabled",
                    name="Constant speed",
                ),
                entity_category=EntityCategory.CONFIG,
                keys=["constant_speed", "enabled"],
            ),
        ]
    )


class FreshIntelliventSkySwitch(
    CoordinatorEntity[DataUpdateCoordinator[FreshIntelliVent]], SwitchEntity
):
    """Fresh Intellivent Sky numbers for the device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: FreshIntelliVent,
        entity_description: SwitchEntityDescription,
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
            hw_version=device.hw_version,
            sw_version=device.fw_version,
        )

    @property
    def is_on(self) -> bool:
        """Return the value reported by the sensor."""
        if self._keys is None:
            return None
        value = self.coordinator.data.modes
        for key in self._keys:
            if value.get(key) is None:
                return None
            value = value[key]

        return cast(bool, value)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on."""
        await self.update_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off."""
        await self.update_state(False)

    async def update_state(self, new_value: bool) -> None:
        """Update state."""
        key = self.entity_description.key

        if key == "constant_speed_enabled":
            self.coordinator.hass.data[CONSTANT_SPEED_UPDATE] = {
                ENABLED_KEY: new_value,
                RPM_KEY: self.device.modes["constant_speed"][RPM_KEY],
            }

        await self.coordinator.async_request_refresh()
