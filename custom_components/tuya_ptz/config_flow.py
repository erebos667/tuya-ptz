import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_CAMERA_NAME, CONF_DEVICE_ID, DOMAIN

class TuyaPTZConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_CAMERA_NAME],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_CAMERA_NAME): str,
                vol.Required(CONF_DEVICE_ID): str,
            }),
            errors=errors,
        )
