"""Services for continuous Tuya PTZ control."""

import voluptuous as vol

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

DIRECTIONS = {
    "up": "0",
    "up_right": "1",
    "right": "2",
    "down_right": "3",
    "down": "4",
    "down_left": "5",
    "left": "6",
    "up_left": "7",
}

MOVE_SCHEMA = vol.Schema(
    {
        vol.Required("direction"): vol.In(DIRECTIONS),
        vol.Required("phase"): vol.In(["start", "stop"]),
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
    }
)


def _tuya_device_id_from_entity(hass: HomeAssistant, entity_id: str) -> str | None:
    """Resolve a Tuya device ID from a Home Assistant entity."""
    entity_entry = dr.async_get(hass).async_get_entity_id(entity_id)
    if entity_entry is None:
        return None
    device_id = entity_entry.device_id
    if not device_id:
        return None
    device_entry = dr.async_get(hass).async_get(device_id)
    if device_entry is None:
        return None
    for domain, identifier in device_entry.identifiers:
        if domain == "tuya":
            return identifier
    return None


async def async_handle_move(call: ServiceCall) -> None:
    """Start or stop a continuous PTZ movement."""
    entity_ids = call.data.get(ATTR_ENTITY_ID, [])
    if not entity_ids:
        raise ValueError("tuya_ptz.move requires a target camera entity")

    tuya_device_id = _tuya_device_id_from_entity(call.hass, entity_ids[0])
    if not tuya_device_id:
        raise ValueError("Target entity is not a Tuya device")

    direction = call.data["direction"]
    phase = call.data["phase"]

    for entry in call.hass.config_entries.async_loaded_entries("tuya"):
        manager = entry.runtime_data.manager
        device = manager.device_map.get(tuya_device_id)
        if device is None:
            continue

        code = "ptz_stop" if phase == "stop" else "ptz_control"
        value = True if phase == "stop" else DIRECTIONS[direction]
        await call.hass.async_add_executor_job(
            manager.send_commands,
            device.id,
            [{"code": code, "value": value}],
        )
        return

    raise ValueError(f"Tuya device {tuya_device_id} is not available")


def async_setup_services(hass: HomeAssistant) -> None:
    """Register PTZ services."""
    if hass.services.has_service(DOMAIN, "move"):
        return
    hass.services.async_register(
        DOMAIN,
        "move",
        async_handle_move,
        schema=MOVE_SCHEMA,
    )
