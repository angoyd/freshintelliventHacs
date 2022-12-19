"""Support for sensors."""
from __future__ import annotations

import logging

from pyfreshintellivent import FreshIntelliVent

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, REVOLUTIONS_PER_MINUTE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN

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
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    device_class=SensorDeviceClass.TEMPERATURE,
                    key="temperature",
                    name="Temperature",
                    native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    device_class=SensorDeviceClass.HUMIDITY,
                    key="humidity",
                    name="Humidity",
                    native_unit_of_measurement=PERCENTAGE,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="rpm",
                    name="Current speed",
                    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="mode",
                    name="Mode",
                    state_class=SensorStateClass.MEASUREMENT,
                ),
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="mode_raw",
                    name="Mode raw",
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
            ),
        ]
    )


class FreshIntelliventSkySensor(
    CoordinatorEntity[DataUpdateCoordinator[FreshIntelliVent]], SensorEntity
):
    """Fresh Intellivent sensors for the device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: FreshIntelliVent,
        entity_description: SensorEntityDescription,
        entity_category: EntityCategory | None = None,
        keys: list | None = None,
    ) -> None:
        """Populate the airthings entity with relevant data."""
        super().__init__(coordinator)
        self.entity_description = entity_description

        name = f"{device.name}"

        self._attr_unique_id = f"{name}_{entity_description.key}"
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
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self.coordinator.data.sensors.as_dict()[self.entity_description.key]
