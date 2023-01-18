"""Config flow for Fresh Intellivent Sky integration."""
from __future__ import annotations

import dataclasses
import logging
from typing import Any, cast

import voluptuous as vol
from bleak import BleakError
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (BluetoothServiceInfo,
                                                async_discovered_service_info)
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from pyfreshintellivent import FreshIntelliVent
from pyfreshintellivent.helpers import validated_authentication_code
from voluptuous.validators import All, Range

from .const import (CONF_AUTH_KEY, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL,
                    DOMAIN, NAME)

_LOGGER = logging.getLogger(__name__)


@dataclasses.dataclass
class Discovery:
    """A discovered bluetooth device."""

    name: str
    discovery_info: BluetoothServiceInfo
    device: FreshIntelliVent


def get_name(device: FreshIntelliVent) -> str:
    """Generate name with identifier for device."""
    return f"{device.manufacturer} {device.name}"


class FreshIntelliventSkyDeviceUpdateError(Exception):
    """Custom error class for device updates."""


class FreshIntelliventSkyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Fresh Intellivent Sky."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_device: Discovery | None = None
        self._discovered_devices: dict[str, Discovery] = {}

    async def _get_device_data(
        self, discovery_info: BluetoothServiceInfo
    ) -> FreshIntelliVent:
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, discovery_info.address
        )
        if ble_device is None:
            raise FreshIntelliventSkyDeviceUpdateError("No ble_device")

        client = FreshIntelliVent()

        error = None

        try:
            await client.connect(ble_device, 30.0)
            await client.fetch_device_information()
        except BleakError as err:
            _LOGGER.error(
                "Error connecting to and getting data from %s: %s",
                discovery_info.address,
                err,
            )
            error = FreshIntelliventSkyDeviceUpdateError("Failed getting device data")
        except Exception as err:
            _LOGGER.error(
                "Unknown error occurred from %s: %s", discovery_info.address, err
            )
            error = err
        finally:
            await client.disconnect()

        if error is not None:
            raise error

        return client

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfo
    ) -> FlowResult:
        """Handle the bluetooth discovery step."""
        _LOGGER.debug("Discovered BT device: %s", discovery_info)
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        try:
            device = await self._get_device_data(discovery_info)
        except FreshIntelliventSkyDeviceUpdateError:
            return self.async_abort(reason="cannot_connect")
        except Exception:  # pylint: disable=broad-except
            return self.async_abort(reason="unknown")

        name = get_name(device)
        self.context["title_placeholders"] = {"name": name}
        self._discovered_device = Discovery(name, discovery_info, device)

        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is None:
            self._set_confirm_only()
            return self.async_show_form(
                step_id="bluetooth_confirm",
                description_placeholders=self.context["title_placeholders"],
            )

        return await self.async_step_auth()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the user step to pick discovered device."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            discovery = self._discovered_devices[address]

            self.context["title_placeholders"] = {
                "name": discovery.name,
            }
            self._discovered_device = discovery

            return await self.async_step_auth()

        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass):
            address = discovery_info.address
            if address in current_addresses or address in self._discovered_devices:
                continue

            if discovery_info.name != NAME:
                continue

            try:
                device = await self._get_device_data(discovery_info)
            except FreshIntelliventSkyDeviceUpdateError:
                return self.async_abort(reason="cannot_connect")
            except Exception:  # pylint: disable=broad-except
                return self.async_abort(reason="unknown")
            name = get_name(device)
            self._discovered_devices[address] = Discovery(name, discovery_info, device)

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        titles = {
            address: get_name(discovery.device)
            for (address, discovery) in self._discovered_devices.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(titles)},
            ),
        )

    async def async_step_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Get auth key."""
        errors = {}
        if user_input is not None:
            auth_key = user_input.get(CONF_AUTH_KEY)

            try:
                if auth_key is not None:
                    validated_authentication_code(auth_key)
            except (TypeError, ValueError) as err:
                _LOGGER.debug(err)
                errors["base"] = err
            else:
                return self.async_create_entry(
                    title=self.context["title_placeholders"]["name"],
                    data={CONF_AUTH_KEY: auth_key},
                )

        return self.async_show_form(
            step_id="auth",
            description_placeholders=self.context["title_placeholders"],
            data_schema=vol.Schema({vol.Optional(CONF_AUTH_KEY): str}),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return FreshIntelliventSkyOptionsFlowHandler(config_entry)


class FreshIntelliventSkyOptionsFlowHandler(OptionsFlow):  # type: ignore[misc]
    """Fresh Intellivent Sky options flow."""

    def __init__(self, config_entry: ConfigEntry):
        """Initialize a Fresh Intellivent Sky options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Manage the options."""
        if user_input is not None:
            return cast(
                dict[str, Any], self.async_create_entry(title="", data=user_input)
            )

        schema: dict[Any, Any] = {
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self._config_entry.options.get(
                    CONF_SCAN_INTERVAL,
                    DEFAULT_SCAN_INTERVAL,
                ),
            ): All(int, Range(min=5)),
        }

        return cast(
            dict[str, Any],
            self.async_show_form(step_id="init", data_schema=vol.Schema(schema)),
        )
