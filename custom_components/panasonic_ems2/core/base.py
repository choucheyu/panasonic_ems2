"""the Panasonic Smart Home Base Entity."""
from __future__ import annotations

import asyncio
from abc import ABC
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


def get_key_from_dict(dictionary, value):
    """Get a key from a dictionary by value."""
    for key, val in dictionary.items():
        if value == val:
            return key
    return None


class PanasonicBaseEntity(CoordinatorEntity, ABC):
    def __init__(
        self,
        coordinator,
        device_gwid,
        device_id,
        client,
        info,
    ):
        super().__init__(coordinator)
        self.client = client
        self.device_gwid = device_gwid
        self.info = info
        self.coordinator = coordinator

        self.device_id = int(device_id)

    @property
    def model(self) -> str:
        return self.info["Model"]

    @property
    def name(self) -> str:
        return self.info["NickName"]

    @property
    def unique_id(self) -> str:
        return self.info["GWID"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, str(self.device_gwid))},
#            configuration_url="http://{}".format(self.info.get("GWIP", "")),
            name=self.info["NickName"],
            manufacturer=f"Panasonic {self.info['ModelType']}",
            model=self.model,
#            sw_version=module.get("firmware_version", ""),
            hw_version=self.info["ModelID"]
        )

    @property
    def available(self) -> bool:
        info = self.info
        coordinator_data = getattr(getattr(self, "coordinator", None), "data", None)
        if isinstance(coordinator_data, dict):
            latest_info = coordinator_data.get(self.device_gwid)
            if isinstance(latest_info, dict):
                info = latest_info

        for device in info.get("Devices", []):
            if not isinstance(device, dict):
                continue
            device_id = device.get("DeviceID", None)
            if device_id is None:
                continue
            try:
                is_matching_device = self.device_id == int(device_id)
            except (TypeError, ValueError):
                is_matching_device = False
            if is_matching_device:
                return bool(device.get("IsAvailable", False))
        return False

    def get_status(self, info):
        """
        get the status from devices info
        """
        if "Information" not in info.get(self.device_gwid, {}):
            return {}
        for device in info[self.device_gwid]["Information"]:
            if self.device_id == device.get("DeviceID", None):
                return device["status"]
        return {}


class PanasonicDescribedEntity(PanasonicBaseEntity):
    """Base for entities backed by a Panasonic entity description."""

    def __init__(
        self,
        coordinator,
        device_gwid,
        device_id,
        client,
        info,
        description,
    ):
        super().__init__(coordinator, device_gwid, device_id, client, info)
        self.entity_description = description

    def _entity_name_suffix(self) -> str:
        """Return the entity-specific suffix after the Panasonic device nickname."""
        name = self.client.get_command_name(self.device_gwid, self.entity_description.key)
        if name is not None:
            return name
        return self.entity_description.name

    @property
    def name(self) -> str:
        """Return the entity display name."""
        return "{} {}".format(
            self.info["NickName"], self._entity_name_suffix()
        )

    @property
    def unique_id(self) -> str:
        """Return the unique ID of the described entity."""
        return "{}_{}_{}".format(
            self.device_gwid,
            self.device_id,
            self.entity_description.key
        )


class PanasonicRangeMixin:
    """Helpers for cloud-provided and static option/range metadata."""

    entity_description: Any

    def _get_options_range(self) -> dict[str, int]:
        """Return option label -> integer value mapping for this description."""
        rng = self.client.get_range(self.device_gwid, self.entity_description.key)
        if len(rng) >= 1:
            return dict(rng)

        range_map: dict[str, int] = {}
        options = list(getattr(self.entity_description, "options", ()) or ())
        option_values = list(getattr(self.entity_description, "options_value", ()) or ())
        for idx, option in enumerate(options):
            try:
                range_map[option] = int(option_values[idx])
            except (IndexError, TypeError, ValueError):
                continue
        return range_map

    def _option_for_value(self, value) -> str | None:
        """Return the option label for an integer-ish Panasonic raw value."""
        try:
            raw_value = int(value)
        except (TypeError, ValueError):
            return None
        return get_key_from_dict(self._get_options_range(), raw_value)


class PanasonicWritableEntityMixin:
    """Shared set-device/update/write-state flow for writable entities."""

    async def async_set_device_value(self, value, refresh_delay: float = 0) -> None:
        """Set a Panasonic command value, refresh the device, and write HA state."""
        await self.client.set_device(
            self.device_gwid,
            self.device_id,
            self.entity_description.key,
            int(value),
        )
        if refresh_delay:
            await asyncio.sleep(refresh_delay)
        await self.client.update_device(self.device_gwid, self.device_id)
        self.async_write_ha_state()
