""" Panasonic Smart Home Binary Sensor"""
import logging
from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity
)

from .core.base import PanasonicDescribedEntity
from .core.const import (
    DOMAIN,
    DATA_CLIENT,
    DATA_COORDINATOR,
    SAA_BINARY_SENSORS,
    PanasonicBinarySensorDescription
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

                for saa, sensors in SAA_BINARY_SENSORS.items():
                    if device_type == saa:
                        for description in sensors:
                            if description.key in status:
                                entities.extend(
                                    [PanasonicBinarySensor(
                                        coordinator, device_gwid, device_id, client, info, description)]
                                )

        async_add_entities(entities)
    except AttributeError as ex:
        _LOGGER.error(ex)

    return True

class PanasonicBinarySensor(PanasonicDescribedEntity, BinarySensorEntity):
    """Implementation of a Panasonic binary sensor."""
    entity_description: PanasonicBinarySensorDescription

    @property
    def is_on(self) -> bool:
        """Return the state of the binary sensor."""
        status = self.get_status(self.coordinator.data)
        value = status.get(self.entity_description.key, False)
        return value
