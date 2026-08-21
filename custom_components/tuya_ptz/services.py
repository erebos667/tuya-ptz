"""Services for Tuya PTZ control and stream diagnostics."""

import logging
from urllib.parse import urlsplit

import voluptuous as vol

from homeassistant.components import persistent_notification
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .const import CONF_DEVICE_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

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
        vol.Optional("camera_entity"): cv.entity_id,
    }
)

DIAGNOSE_STREAM_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
        vol.Optional("camera_entity"): cv.entity_id,
    }
)


def _tuya_device_id_from_entity(hass: HomeAssistant, entity_id: str) -> str | None:
    """Resolve a Tuya device ID from a Home Assistant entity."""
    entity_entry = er.async_get(hass).async_get(entity_id)
    if entity_entry is None or entity_entry.device_id is None:
        return None
    device_entry = dr.async_get(hass).async_get(entity_entry.device_id)
    if device_entry is None:
        return None
    for domain, identifier in device_entry.identifiers:
        if domain == "tuya":
            return identifier
    return None


def _default_device_id(hass: HomeAssistant) -> str | None:
    """Use the configured PTZ camera when no target is supplied."""
    entries = list(hass.config_entries.async_entries(DOMAIN))
    if len(entries) == 1:
        return entries[0].data.get(CONF_DEVICE_ID)
    return None


def _target_device_id(hass: HomeAssistant, call: ServiceCall) -> str | None:
    """Resolve the Tuya device targeted by a service call."""
    camera_entity = call.data.get("camera_entity")
    if camera_entity:
        return _tuya_device_id_from_entity(hass, camera_entity)
    entity_ids = call.data.get(ATTR_ENTITY_ID, [])
    if entity_ids:
        return _tuya_device_id_from_entity(hass, entity_ids[0])
    return _default_device_id(hass)


def _get_tuya_manager_and_device(hass: HomeAssistant, tuya_device_id: str):
    """Find the loaded Tuya manager and device."""
    for entry in hass.config_entries.async_loaded_entries("tuya"):
        manager = entry.runtime_data.manager
        device = manager.device_map.get(tuya_device_id)
        if device is not None:
            return manager, device
    return None, None


def _notify(hass: HomeAssistant, message: str) -> None:
    """Show diagnostic results without exposing credentials."""
    persistent_notification.async_create(
        hass,
        message,
        title="Tuya PTZ – diagnostic flux",
        notification_id="tuya_ptz_stream_diagnostic",
    )


async def async_handle_move(call: ServiceCall) -> None:
    """Start or stop a continuous PTZ movement."""
    tuya_device_id = _target_device_id(call.hass, call)
    if not tuya_device_id:
        raise ValueError(
            "tuya_ptz.move needs a target camera when multiple PTZ cameras are configured"
        )
    manager, device = _get_tuya_manager_and_device(call.hass, tuya_device_id)
    if manager is None or device is None:
        raise ValueError(f"Tuya device {tuya_device_id} is not available")
    code = "ptz_stop" if call.data["phase"] == "stop" else "ptz_control"
    value = True if call.data["phase"] == "stop" else DIRECTIONS[call.data["direction"]]
    await call.hass.async_add_executor_job(
        manager.send_commands, device.id, [{"code": code, "value": value}]
    )


async def async_handle_diagnose_stream(call: ServiceCall) -> None:
    """Ask Tuya for the same RTSP stream source used by Home Assistant."""
    try:
        tuya_device_id = _target_device_id(call.hass, call)
        if not tuya_device_id:
            message = (
                "Impossible de déterminer la caméra cible. "
                "Avec plusieurs caméras PTZ, renseigne camera_entity."
            )
            _notify(call.hass, message)
            _LOGGER.error(message)
            return

        manager, device = _get_tuya_manager_and_device(call.hass, tuya_device_id)
        if manager is None or device is None:
            message = (
                f"L'appareil Tuya {tuya_device_id} n'est pas disponible dans "
                "l'intégration Tuya chargée."
            )
            _notify(call.hass, message)
            _LOGGER.error(message)
            return

        try:
            stream_url = await call.hass.async_add_executor_job(
                manager.get_device_stream_allocate, device.id, "rtsp"
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception(
                "Tuya PTZ stream diagnostic failed for %s (%s)",
                device.product_name,
                device.id,
            )
            _notify(
                call.hass,
                f"Tuya n'a pas pu allouer le flux RTSP pour « {device.product_name} ».\n\n"
                f"Erreur : {type(err).__name__}: {err}",
            )
            return

        if not stream_url:
            message = f"Tuya n'a retourné aucune URL RTSP pour « {device.product_name} »."
            _notify(call.hass, message)
            _LOGGER.warning(message)
            return

        parsed = urlsplit(stream_url)
        safe_url = parsed._replace(query="", fragment="").geturl()
        message = (
            f"Caméra : {device.product_name}\n"
            f"Protocole : {parsed.scheme}\n"
            f"Serveur : {parsed.hostname}\n"
            f"Port : {parsed.port}\n"
            f"Chemin : {parsed.path}\n\n"
            "Les paramètres d'authentification de l'URL ont été masqués.\n"
            f"Source : {safe_url}"
        )
        _notify(call.hass, message)
        _LOGGER.warning(
            "Tuya PTZ stream diagnostic for %s (%s): RTSP source=%s | scheme=%s host=%s port=%s path=%s | query parameters redacted",
            device.product_name,
            device.id,
            safe_url,
            parsed.scheme,
            parsed.hostname,
            parsed.port,
            parsed.path,
        )
    except Exception as err:  # noqa: BLE001
        _LOGGER.exception("Unexpected Tuya PTZ stream diagnostic error")
        _notify(
            call.hass,
            f"Erreur interne du diagnostic Tuya PTZ : {type(err).__name__}: {err}",
        )


def async_setup_services(hass: HomeAssistant) -> None:
    """Register PTZ services."""
    if hass.services.has_service(DOMAIN, "move"):
        return
    hass.services.async_register(DOMAIN, "move", async_handle_move, schema=MOVE_SCHEMA)
    hass.services.async_register(
        DOMAIN,
        "diagnose_stream",
        async_handle_diagnose_stream,
        schema=DIAGNOSE_STREAM_SCHEMA,
    )
