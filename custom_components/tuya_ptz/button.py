"""PTZ direction buttons for Tuya cameras."""

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_CAMERA_NAME, CONF_DEVICE_ID, DOMAIN

DIRECTIONS = {
    "Up": ("0", "mdi:arrow-up"),
    "Up Right": ("1", "mdi:arrow-top-right"),
    "Right": ("2", "mdi:arrow-right"),
    "Down Right": ("3", "mdi:arrow-bottom-right"),
    "Down": ("4", "mdi:arrow-down"),
    "Down Left": ("5", "mdi:arrow-bottom-left"),
    "Left": ("6", "mdi:arrow-left"),
    "Up Left": ("7", "mdi:arrow-top-left"),
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Create PTZ controls."""
    data = hass.data[DOMAIN][entry.entry_id]
    device_id = data[CONF_DEVICE_ID]
    camera_name = data[CONF_CAMERA_NAME]

    entities = [
        TuyaPTZButton(
            hass,
            entry.entry_id,
            device_id,
            camera_name,
            action_name,
            direction,
            icon,
        )
        for action_name, (direction, icon) in DIRECTIONS.items()
    ]
    entities.append(
        TuyaPTZButton(
            hass,
            entry.entry_id,
            device_id,
            camera_name,
            "Stop",
            None,
            "mdi:stop",
        )
    )
    async_add_entities(entities)


class TuyaPTZButton(ButtonEntity):
    """A single Tuya PTZ command button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass,
        entry_id,
        device_id,
        camera_name,
        action_name,
        direction,
        icon,
    ):
        self.hass = hass
        self._device_id = device_id
        self._direction = direction
        self._attr_name = f"PTZ {action_name}"
        self._attr_unique_id = (
            f"{entry_id}_ptz_{action_name.lower().replace(' ', '_')}"
        )
        self._attr_icon = icon
        self._attr_device_info = DeviceInfo(
            identifiers={("tuya", device_id)},
            name=camera_name,
            manufacturer="Tuya",
        )

    async def async_press(self) -> None:
        """Send the selected PTZ command through the existing Tuya manager."""
        manager = None
        device = None

        for entry in self.hass.config_entries.async_loaded_entries("tuya"):
            candidate_manager = entry.runtime_data.manager
            if self._device_id in candidate_manager.device_map:
                manager = candidate_manager
                device = candidate_manager.device_map[self._device_id]
                break

        if manager is None or device is None:
            raise RuntimeError(
                f"Tuya device {self._device_id} is not available"
            )

        if self._direction is None:
            commands = [{"code": "ptz_stop", "value": True}]
        else:
            commands = [{"code": "ptz_control", "value": self._direction}]

        await self.hass.async_add_executor_job(
            manager.send_commands,
            device.id,
            commands,
        )
