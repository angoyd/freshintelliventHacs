"""Support for sensors."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity, SelectEntityDescription
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
from pyfreshintellivent.helpers import DETECTION_HIGH, DETECTION_LOW, DETECTION_MEDIUM

from .const import (
    DETECTION_OFF,
    DOMAIN,
    HUMIDITY_MODE_UPDATE,
    LIGHT_AND_VOC_MODE_UPDATE,
    DETECTION_KEY,
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
            FreshIntelliventSkySelect(
                coordinator,
                coordinator.data,
                SelectEntityDescription(
                    key="humidity_detection",
                    name="Humidity detection",
                ),
                keys=["humidity", DETECTION_KEY],
            ),
            FreshIntelliventSkySelect(
                coordinator,
                coordinator.data,
                SelectEntityDescription(
                    key="light_detection",
                    name="Light detection",
                ),
                keys=["light_and_voc", "light", DETECTION_KEY],
            ),
            FreshIntelliventSkySelect(
                coordinator,
                coordinator.data,
                SelectEntityDescription(
                    key="voc_detection",
                    name="VOC detection",
                ),
                keys=["light_and_voc", "voc", DETECTION_KEY],
            ),
        ]
    )


class FreshIntelliventSkySelect(
    CoordinatorEntity[DataUpdateCoordinator[FreshIntelliVent]], SelectEntity
):
    """Fresh Intellivent Sky numbers for the device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: FreshIntelliVent,
        entity_description: SelectEntityDescription,
        keys: list | None = None,
    ) -> None:
        """Populate the airthings entity with relevant data."""
        super().__init__(coordinator)
        self.entity_description = entity_description

        self.device = device

        name = f"{device.manufacturer} {device.name}"

        self._attr_unique_id = f"{device.manufacturer}_{name}_{entity_description.key}"
        self._attr_entity_category = EntityCategory.CONFIG
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
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        if self.entity_description.key == "light_detection":
            return [DETECTION_OFF, DETECTION_MEDIUM, DETECTION_HIGH]
        return [DETECTION_OFF, DETECTION_LOW, DETECTION_MEDIUM, DETECTION_HIGH]

    @property
    def current_option(self) -> str | None:
        """Return the value reported value."""
        if self._keys is None:
            return None
        value = self.coordinator.data.modes
        for key in self._keys:
            if value.get(key) is None:
                return None
            value = value[key]

        return value

    async def async_select_option(self, option: str) -> None:
        """Set the option."""
        enabled = option == DETECTION_OFF
        key = self.entity_description.key

        if key == "humidity_detection":
            self.coordinator.hass.data[HUMIDITY_MODE_UPDATE] = {
                "enabled": enabled,
                "detection": option,
                "rpm": self.device.modes["humidity"]["rpm"],
            }
        else:
            light = self.device.modes["light_and_voc"]["light"]
            light_detection = light["detection"]
            light_enabled = light["enabled"]

            voc = self.device.modes["light_and_voc"]["voc"]
            voc_enabled = voc["enabled"]
            voc_detection = voc["detection"]

            if key == "light_detection":
                light_enabled = enabled

                # Detection `off` is not supported. Use `enabled=false` instead.
                # We can reuse the last option to fix this.
                if option != DETECTION_OFF:
                    light_detection = option
            else:
                voc_enabled = enabled

                # Detection `off` is not supported. Use `enabled=false` instead.
                # We can reuse the last option to fix this.
                if option != DETECTION_OFF:
                    voc_detection = option

            self.coordinator.hass.data[LIGHT_AND_VOC_MODE_UPDATE] = {
                "light_enabled": light_enabled,
                "light_detection": light_detection,
                "voc_enabled": voc_enabled,
                "voc_detection": voc_detection,
            }

        await self.coordinator.async_request_refresh()
