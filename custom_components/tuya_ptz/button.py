from homeassistant.components.button import ButtonEntity
from homeassistant.helpers import device_registry as dr

from .const import CONF_CAMERA_NAME, CONF_DEVICE_ID, DOMAIN

DIRECTIONS = {
    "Up": "0",
    "Up Right": "1",
    "Right": "2",
    "Down Right": "3",
    "Down": "4",
    "Down Left": "5",
    "Left": "6",
    "Up Left": "7",
}

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    device_id = data[CONF_DEVICE_ID]
    camera_name = data[CONF_CAMERA_NAME]
    dev = dr.async_get(hass).async_get_device({(DOMAIN, device_id)})

    entities = [
        TuyaPTZButton(hass, entry.entry_id, device_id, camera_name, key, value, dev.id if dev else None)
        for key, value in DIRECTIONS.items()
    ]
    entities.append(TuyaPTZButton(hass, entry.entry_id, device_id, camera_name, "Stop", None, dev.id if dev else None))
    async_add_entities(entities)

class TuyaPTZButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, hass, entry_id, device_id, camera_name, action_name, direction, device_registry_id):
        self.hass = hass
        self._device_id = device_id
        self._direction = direction
        self._attr_name = f"PTZ {action_name}"
        self._attr_unique_id = f"{entry_id}_ptz_{action_name.lower().replace(' ', '_')}"
        self._attr_device_info = None
        if device_registry_id:
            self._attr_device_info = {"identifiers": {(DOMAIN, device_id)}}

    async def async_press(self):
        if self._direction is None:
            await self._set_stop()
            return
        await self._set_dp("ptz_control", self._direction)

    async def _set_stop(self):
        await self._set_dp("ptz_stop", True)

    async def _set_dp(self, code, value):
        # The current Tuya integration keeps the cloud API client in the Tuya entry.
        # Resolve it from the existing loaded Tuya integration rather than asking for credentials again.
        tuya_data = self.hass.data.get("tuya") or {}
        # Different HA releases store the Tuya manager under different keys/objects.
        # Try common manager shapes and fail with an actionable error if unavailable.
        manager = tuya_data.get("manager")
        if manager is None:
            for value_obj in tuya_data.values():
                if hasattr(value_obj, "set_dp") or hasattr(value_obj, "async_set_dp"):
                    manager = value_obj
                    break
        if manager is None:
            raise RuntimeError("Unable to access the Home Assistant Tuya manager")

        method = getattr(manager, "async_set_dp", None) or getattr(manager, "set_dp", None)
        if method is None:
            raise RuntimeError("The installed Home Assistant Tuya integration does not expose a DP command method")

        result = method(self._device_id, code, value)
        if hasattr(result, "__await__"):
            await result
