"""Support for sensors."""
from __future__ import annotations

import logging

from pyfreshintellivent import FreshIntelliVent

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    TIME_MINUTES,
    UnitOfTemperature,
)
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
                    key="mode", name="Mode", state_class=SensorStateClass.MEASUREMENT
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
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="humidity_detection",
                    name="Humidity detection",
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
                is_sensor=False,
                keys=["humidity", "detection"],
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="humidity_and_voc_speed",
                    name="Humidity and VOC speed",
                    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
                is_sensor=False,
                keys=["humidity", "rpm"],
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="light_detection",
                    name="Light detection",
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
                is_sensor=False,
                keys=["light_and_voc", "light", "detection"],
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="voc_detection",
                    name="VOC detection",
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
                is_sensor=False,
                keys=["light_and_voc", "voc", "detection"],
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="constant_speed_speed",
                    name="Constant speed speed",
                    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
                is_sensor=False,
                keys=["constant_speed", "rpm"],
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="airing speed",
                    name="Airing speed",
                    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
                is_sensor=False,
                keys=["airing", "rpm"],
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="timer_and_light",
                    name="Timer and light",
                    native_unit_of_measurement=REVOLUTIONS_PER_MINUTE,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
                is_sensor=False,
                keys=["timer", "rpm"],
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="timer_minutes",
                    name="Timer minutes",
                    native_unit_of_measurement=TIME_MINUTES,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
                is_sensor=False,
                keys=["timer", "minutes"],
            ),
            FreshIntelliventSkySensor(
                coordinator,
                coordinator.data,
                SensorEntityDescription(
                    key="timer_delay_minutes",
                    name="Timer delay minutes",
                    native_unit_of_measurement=TIME_MINUTES,
                    state_class=SensorStateClass.MEASUREMENT,
                ),
                EntityCategory.DIAGNOSTIC,
                is_sensor=False,
                keys=["timer", "delay", "minutes"],
            ),
        ]
    )


class FreshIntelliventSkySensor(
    CoordinatorEntity[DataUpdateCoordinator[FreshIntelliVent]], SensorEntity
):
    """Fresh Intellivent sensors for the device."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        device: FreshIntelliVent,
        entity_description: SensorEntityDescription,
        entity_category: EntityCategory | None = None,
        is_sensor: bool = True,
        keys: list | None = None,
    ) -> None:
        """Populate the airthings entity with relevant data."""
        super().__init__(coordinator)
        self.entity_description = entity_description

        name = f"{device.name}"

        self._attr_unique_id = f"{name}_{entity_description.key}"
        self._attr_entity_category = entity_category
        self._is_sensor = is_sensor
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
        if self._is_sensor is True:
            return self.coordinator.data.sensors.as_dict()[self.entity_description.key]

        if self._keys is None:
            return None
        value = self.coordinator.data.modes
        for key in self._keys:
            value = value[key]

        if isinstance(value, str):
            value = value.capitalize()
        return value
