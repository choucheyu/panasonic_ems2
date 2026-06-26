""" Panasonic Smart Home Switch"""
import logging
from datetime import timedelta

from homeassistant.components.switch import (
    SwitchEntity
)
from .core.base import PanasonicDescribedEntity, PanasonicWritableEntityMixin
from .core.const import (
    DOMAIN,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_WASHING_MACHINE,
    LIGHT_POWER,
    LIGHT_OPERATION_STATE,
    WASHING_MACHINE_SWITCHES,
    SAA_SWITCHES,
    PanasonicSwitchDescription
)
SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities) -> bool:
    client = hass.data[DOMAIN][entry.entry_id][DATA_CLIENT]
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    devices = coordinator.data

    try:
        entities = []

        for device_gwid, info in devices.items():
            device_type = int(info.get("DeviceType"))
            if not client.is_supported(info.get("ModelType", "")):
                continue
            for dev in info.get("Information", {}):
                device_id = dev["DeviceID"]
                status = dev["status"]

                for saa, switchs in SAA_SWITCHES.items():
                    if device_type == saa:
                        for description in switchs:
                            if description.key in status:
                                entities.extend(
                                    [PanasonicSwitch(
                                        coordinator, device_gwid, device_id, client, info, description)]
                                )

            if device_type == DEVICE_TYPE_WASHING_MACHINE:
                for description in WASHING_MACHINE_SWITCHES:
                    if True:
                        entities.extend(
                            [PanasonicSwitch(
                                coordinator, device_gwid, 1, client, info, description)]
                        )

        async_add_entities(entities)
    except AttributeError as ex:
        _LOGGER.error(ex)

    return True


class PanasonicSwitch(PanasonicWritableEntityMixin, PanasonicDescribedEntity, SwitchEntity):
    """Implementation of a Panasonic switch."""
    entity_description: PanasonicSwitchDescription

    def _raw_value_to_is_on(self, value: int) -> bool:
        if self.entity_description.reverse_state:
            return int(value) == 0
        return bool(int(value))

    def _is_on_to_raw_value(self, is_on: bool) -> int:
        if self.entity_description.reverse_state:
            return 0 if is_on else 1
        return 1 if is_on else 0

    def _entity_name_suffix(self) -> str:
        """Return the switch-specific name suffix."""
        name = self.client.get_command_name(self.device_gwid, self.entity_description.key)
        if name is not None:
            # hard code
            if "nanoe" in name:
                return self.entity_description.name
            device_name = ""
            for dev in self.info.get("Devices", {}):
                if self.device_id == dev.get("DeviceID", 0):
                    device_name = dev.get("Name", "")
                    break
            return "{}{}".format(device_name, name)
        return self.entity_description.name

    @property
    def is_on(self) -> bool | None:
        device_id = self.device_id
        info = self.coordinator.data
        status = self.get_status(info)

        avaiable = status.get(self.entity_description.key, None)
        if avaiable is None:
            return None

        if ((int(info[self.device_gwid].get("DeviceType")) == DEVICE_TYPE_LIGHT) and
                (self.entity_description.key == LIGHT_POWER)):
            for device in info[self.device_gwid]["Information"]:
                operation_state = device["status"].get(LIGHT_OPERATION_STATE, None)
                if operation_state != None:
                    state = (int(operation_state) & (1 << (device_id - 1))) >> (device_id - 1)
                    return bool(state)
            return None

        state = status.get(self.entity_description.key)
        if not isinstance(state, int):
            return None
        return self._raw_value_to_is_on(int(status.get(self.entity_description.key, 0)))

    async def async_turn_on(self) -> None:
        await self.async_set_device_value(self._is_on_to_raw_value(True), refresh_delay=1)

    async def async_turn_off(self) -> None:
        await self.async_set_device_value(self._is_on_to_raw_value(False), refresh_delay=1)
