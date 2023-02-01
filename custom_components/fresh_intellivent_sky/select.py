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
    ENABLED_KEY,
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
        """Populate the entity with relevant data."""
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
            if key == DETECTION_KEY and value[ENABLED_KEY] == DETECTION_OFF:
                # pyfreshintellivent doesn't support 'off'.
                # Need to check the enabled key as well to see if the mode is 'off'.
                return DETECTION_OFF
            value = value[key]

        return value

    def _detection_off_check(self, new_value: str, previous_value: str) -> str:
        """Detection `off` is not supported. Use `enabled=false` instead.
        # We can reuse the last option to fix this."""
        if new_value != DETECTION_OFF:
            return new_value
        return previous_value

    async def async_select_option(self, option: str) -> None:
        """Set the option."""
        key = self.entity_description.key
        enabled = option != DETECTION_OFF

        if key == "humidity_detection":
            humidity = self.device.modes["humidity"]
            detection = self._detection_off_check(
                new_value=option, previous_value=humidity[DETECTION_KEY]
            )

            self.coordinator.hass.data[HUMIDITY_MODE_UPDATE] = {
                "enabled": enabled,
                "detection": detection,
                "rpm": humidity["rpm"],
            }
        else:
            light = self.device.modes["light_and_voc"]["light"]
            light_enabled = light[ENABLED_KEY]
            light_detection = light[DETECTION_KEY]

            voc = self.device.modes["light_and_voc"]["voc"]
            voc_enabled = voc[ENABLED_KEY]
            voc_detection = voc[DETECTION_KEY]

            if key == "light_detection":
                light_enabled = enabled
                light_detection = self._detection_off_check(
                    new_value=option, previous_value=light_detection
                )
            else:
                voc_enabled = enabled
                voc_detection = self._detection_off_check(
                    new_value=option, previous_value=voc_detection
                )

            self.coordinator.hass.data[LIGHT_AND_VOC_MODE_UPDATE] = {
                "light_enabled": light_enabled,
                "light_detection": light_detection,
                "voc_enabled": voc_enabled,
                "voc_detection": voc_detection,
            }

        await self.coordinator.async_request_refresh()
