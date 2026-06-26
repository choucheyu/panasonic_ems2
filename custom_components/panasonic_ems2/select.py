""" Panasonic Smart Home Select"""
import logging
from datetime import timedelta

from homeassistant.components.select import (
    SelectEntity
)

from .core.base import (
    PanasonicDescribedEntity,
    PanasonicRangeMixin,
    PanasonicWritableEntityMixin,
)
from .core.const import (
    DOMAIN,
    DATA_CLIENT,
    DATA_COORDINATOR,
    SAA_SELECTS,
    DEVICE_TYPE_WASHING_MACHINE,
    WASHING_MACHINE_SELECTS_BY_MODEL,
    PanasonicSelectDescription
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

                for saa, selects in SAA_SELECTS.items():
                    if device_type == saa:
                        for description in selects:
                            if description.key in status:
                                entities.extend(
                                    [PanasonicSelect(
                                        coordinator, device_gwid, device_id, client, info, description)]
                                )

            if device_type == DEVICE_TYPE_WASHING_MACHINE:
                for description in WASHING_MACHINE_SELECTS_BY_MODEL.get(info.get("ModelType", ""), ()):
                        entities.extend(
                            [PanasonicSelect(
                                coordinator, device_gwid, 1, client, info, description)]
                        )

        async_add_entities(entities)
    except AttributeError as ex:
        _LOGGER.error(ex)

    return True


class PanasonicSelect(
    PanasonicRangeMixin,
    PanasonicWritableEntityMixin,
    PanasonicDescribedEntity,
    SelectEntity,
):
    """Implementation of a Panasonic select."""
    entity_description: PanasonicSelectDescription

    @property
    def options(self) -> list:
        """Return a set of selectable options."""
        return list(self._get_options_range().keys())

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        status = self.get_status(self.coordinator.data)
        if status:
            return self._option_for_value(status.get(self.entity_description.key, "0"))
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        value = self._get_options_range()[option]
        await self.async_set_device_value(value)
