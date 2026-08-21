"""Config flow for Tuya PTZ."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_CAMERA_NAME, CONF_DEVICE_ID, DOMAIN


class TuyaPTZConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Tuya PTZ setup."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Select a Tuya camera exposing PTZ controls."""
        devices: dict[str, str] = {}

        for entry in self.hass.config_entries.async_entries("tuya"):
            runtime_data = getattr(entry, "runtime_data", None)
            manager = getattr(runtime_data, "manager", None)
            if manager is None:
                continue

            device_map = getattr(manager, "device_map", {}) or {}
            for device in device_map.values():
                function = getattr(device, "function", {}) or {}
                if not isinstance(function, dict):
                    continue
                if "ptz_control" not in function or "ptz_stop" not in function:
                    continue

                device_id = getattr(device, "id", None)
                if not device_id:
                    continue
                devices[device_id] = getattr(device, "name", None) or device_id

        if not devices:
            return self.async_abort(reason="no_ptz_cameras")

        if user_input:
            device_id = user_input[CONF_DEVICE_ID]
            await self.async_set_unique_id(f"{DOMAIN}_{device_id}")
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
        )
