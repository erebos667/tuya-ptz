"""Config flow for Tuya PTZ."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_CAMERA_NAME, CONF_DEVICE_ID, DOMAIN


class TuyaPTZConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Tuya PTZ setup."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Select a Tuya camera exposing PTZ controls."""
        errors = {}
        devices = {}

        for entry in self.hass.config_entries.async_loaded_entries("tuya"):
            manager = entry.runtime_data.manager
            for device in manager.device_map.values():
                if "ptz_control" not in device.function or "ptz_stop" not in device.function:
                    continue
                devices[device.id] = device.name or device.id

        if not devices:
            return self.async_abort(reason="no_ptz_cameras")

        if user_input:
            device_id = user_input[CONF_DEVICE_ID]
            await self.async_set_unique_id(device_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=devices.get(device_id, device_id),
                data={
                    CONF_DEVICE_ID: device_id,
                    CONF_CAMERA_NAME: devices.get(device_id, device_id),
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE_ID): vol.In(devices)}
            ),
            errors=errors,
        )
