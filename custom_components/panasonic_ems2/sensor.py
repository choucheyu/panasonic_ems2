""" Panasonic Smart Home Sensor"""
import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity
)

from .core.base import PanasonicDescribedEntity, PanasonicRangeMixin
from .core.const import (
    DOMAIN,
    DATA_CLIENT,
    DATA_COORDINATOR,
    SAA_SENSORS,
    DEVICE_TYPE_FRIDGE,
    DEVICE_TYPE_WASHING_MACHINE,
    DEVICE_TYPE_WEIGHT_PLATE,
    WASHING_MACHINE_ACTIVE_FINISH_TIME_KEYS,
    WASHING_MACHINE_ACTIVE_OPERATING_STATUS_VALUES,
    WASHING_MACHINE_CLOCK_TIME_KEYS,
    WASHING_MACHINE_OPERATING_STATUS,
    WASHING_MACHINE_RESERVATION_CLOCK_TIME_KEYS,
    WASHING_MACHINE_RESERVATION_OPERATING_STATUS_VALUES,
    WASHING_MACHINE_SENSORS,
    WASHING_MACHINE_SENSORS_BY_MODEL,
    WEIGHT_PLATE_SENSORS,
    PanasonicSensorDescription
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

                for saa, sensors in SAA_SENSORS.items():
                    if device_type == saa:
                        for description in sensors:
                            if description.key in status:
                                entities.extend(
                                    [PanasonicSensor(
                                        coordinator, device_gwid, device_id, client, info, description)]
                                )

            if device_type == DEVICE_TYPE_WASHING_MACHINE:
                for description in WASHING_MACHINE_SENSORS:
                        entities.extend(
                            [PanasonicSensor(
                                coordinator, device_gwid, 1, client, info, description)]
                        )
                for description in WASHING_MACHINE_SENSORS_BY_MODEL.get(info.get("ModelType", ""), ()):
                        entities.extend(
                            [PanasonicSensor(
                                coordinator, device_gwid, 1, client, info, description)]
                        )

            if device_type == DEVICE_TYPE_WEIGHT_PLATE:
                for description in WEIGHT_PLATE_SENSORS:
                        entities.extend(
                            [PanasonicSensor(
                                coordinator, device_gwid, 1, client, info, description)]
                        )

        async_add_entities(entities)
    except AttributeError as ex:
        _LOGGER.error(ex)

    return True

class PanasonicSensor(PanasonicRangeMixin, PanasonicDescribedEntity, SensorEntity):
    """Implementation of a Panasonic sensor."""
    entity_description: PanasonicSensorDescription

    @property
    def native_value(self):
        """Return the state of the sensor."""
        status = self.get_status(self.coordinator.data)
        if self.entity_description.device_class == SensorDeviceClass.ENUM:
            rng = self._get_options_range()
            value = status.get(self.entity_description.key, 0)
            if len(rng) >= 1:
                return self._option_for_value(value)
            return value
        value = status.get(self.entity_description.key, None)

        if self.entity_description.key in WASHING_MACHINE_CLOCK_TIME_KEYS:
            operating_status_value = status.get(WASHING_MACHINE_OPERATING_STATUS)
            if operating_status_value is None:
                return None
            try:
                operating_status = int(operating_status_value)
            except (TypeError, ValueError):
                return None

            if (
                self.entity_description.key in WASHING_MACHINE_ACTIVE_FINISH_TIME_KEYS
                and operating_status not in WASHING_MACHINE_ACTIVE_OPERATING_STATUS_VALUES
            ):
                return None
            if (
                self.entity_description.key in WASHING_MACHINE_RESERVATION_CLOCK_TIME_KEYS
                and operating_status not in WASHING_MACHINE_RESERVATION_OPERATING_STATUS_VALUES
            ):
                return None

            if value is None:
                return None
            try:
                raw_value = int(value)
            except (TypeError, ValueError):
                return value
            # 64933/65535-class values are Panasonic sentinel values seen once the washer starts;
            # do not show them as real clock-time estimates.
            if raw_value >= 60000 or raw_value < 0:
                return None
            return (datetime.now() + timedelta(minutes=raw_value)).strftime("%H:%M")

        device_type = int(self.info.get("DeviceType"))
        if device_type != DEVICE_TYPE_FRIDGE:
            if self.entity_description.device_class == SensorDeviceClass.TEMPERATURE:
                if value < -1 or value > 50:
                    return None
        if device_type == DEVICE_TYPE_FRIDGE:
            if isinstance(value, str):
                if "-" in value:
                    value = value.replace("-", "")
                    value = - float(value) / 1000
                value = float(value)
            if value > 60000:
                value = value - 65535
            elif value > 30000:
                value = value - 32768
            elif value > 200:
                value = value - 255
        if self.entity_description.device_class == SensorDeviceClass.HUMIDITY:
            if value < 30:
                return None
        if self.entity_description.device_class == SensorDeviceClass.ENERGY:
            if value is not None:
                if isinstance(value, str):
                    value = float(value.replace("-", ""))
                value = float(value * 0.1)
                if value < 1:
                    return None
        return value

#    async def async_update(self):
#        """Fetch state from the device."""
#        await self.coordinator.async_request_refresh()
