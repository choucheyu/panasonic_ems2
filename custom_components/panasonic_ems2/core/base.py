"""the Panasonic Smart Home Base Entity."""
from abc import ABC, abstractmethod

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    DOMAIN,
)


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
