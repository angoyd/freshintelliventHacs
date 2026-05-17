"""Support for boost button."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from pyfreshintellivent import FreshIntelliVent

from .const import BOOST_UPDATE, DOMAIN, ENABLED_KEY, MINUTES_KEY, RPM_KEY

_LOGGER = logging.getLogger(__name__)

BOOST_DURATION_SECONDS = 600  # 10 minutes


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up buttons dynamically through discovery."""
    coordinator: DataUpdateCoordinator[FreshIntelliVent] = hass.data[DOMAIN][
        config_entry.entry_id
    ]

    async_add_entities(
        [
            FreshIntelliventSkyBoostButton(
                coordinator,
                coordinator.data,
                ButtonEntityDescription(
                    key="boost",
                    name="Boost",
                ),
            ),
        ]
    )


class FreshIntelliventSkyBoostButton(
    CoordinatorEntity[DataUpdateCoordinator[FreshIntelliVent]], ButtonEntity
):
    """Fresh Intellivent Sky boost button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: FreshIntelliVent,
        entity_description: ButtonEntityDescription,
    ) -> None:
        """Populate the entity with relevant data."""
        super().__init__(coordinator)
        self.entity_description = entity_description

        name = f"{device.manufacturer} {device.name}"

        self.device = device
        self._attr_unique_id = f"{device.manufacturer}_{name}_{entity_description.key}"
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

    async def async_press(self) -> None:
        """Handle the button press - trigger boost."""
        self.coordinator.hass.data[BOOST_UPDATE] = {
            ENABLED_KEY: True,
            RPM_KEY: 2400,
            MINUTES_KEY: BOOST_DURATION_SECONDS,
        }
        await self.coordinator.async_request_refresh()
