""" Panasonic Smart Home Number"""
import logging
from datetime import timedelta

from homeassistant.components.number import (
    NumberEntity
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
    SAA_NUMBERS,
    CLIMATE_TIMER_ON,
    CLIMATE_TIMER_OFF,
    PanasonicNumberDescription
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

                for saa, numbers in SAA_NUMBERS.items():
                    if device_type == saa:
                        for description in numbers:
                            if description.key in status:
                                entities.extend(
                                    [PanasonicNumber(
                                        coordinator, device_gwid, device_id, client, info, description)]
                                )

        async_add_entities(entities)
    except AttributeError as ex:
        _LOGGER.error(ex)

    return True


class PanasonicNumber(
    PanasonicRangeMixin,
    PanasonicWritableEntityMixin,
    PanasonicDescribedEntity,
    NumberEntity,
):
    """Implementation of a Panasonic number."""
    entity_description: PanasonicNumberDescription

    def __init__(
        self,
        coordinator,
        device_gwid,
        device_id,
        client,
        info,
        description
    ):
        super().__init__(coordinator, device_gwid, device_id, client, info, description)
        range_values = list(self._get_options_range().values())

        self._attr_native_min_value = 0
        self._attr_native_max_value = 1

        if range_values:
            self._attr_native_min_value = min(range_values)
            self._attr_native_max_value = max(range_values)
        else:
            self._attr_native_min_value = self.entity_description.native_min_value
            self._attr_native_max_value = self.entity_description.native_max_value

    @property
    def native_value(self) -> float | None:
        """Return the value reported by the number."""
        status = self.get_status(self.coordinator.data)
        if status:
            value = float(status[self.entity_description.key])
            if self.entity_description.key in (CLIMATE_TIMER_ON, CLIMATE_TIMER_OFF):
                if value == 65535:
                    return 0
                return int(value)
            return value
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.async_set_device_value(value)
