"""WebSocket API for the Scheduled Scenes Studio."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant

from .config_flow import _validate_input
from .const import (
    CONF_BRIGHTNESS_CURVES,
    CONF_CURVES,
    CONF_NAME,
    CONF_PROGRAMS,
    DOMAIN,
)
from .logic import parse_brightness_curves, parse_dim_to_warm_curves


def _merge_curves(target: dict[str, Any], curves: Any) -> None:
    """Normalize supported named-map and list curve formats for the Studio."""
    if isinstance(curves, dict):
        target.update(curves)
    elif isinstance(curves, list):
        for index, curve in enumerate(curves, start=1):
            if isinstance(curve, dict):
                target[str(curve.get("name", f"curve_{index}"))] = curve


def get_config(hass: HomeAssistant) -> dict[str, Any]:
    """Collect the programs and shared curves currently stored in config entries."""
    programs = []
    stored_curves = hass.data.get(DOMAIN, {}).get("_studio_curves", {})
    curves: dict[str, Any] = dict(stored_curves.get(CONF_CURVES, {}))
    brightness_curves: dict[str, Any] = dict(
        stored_curves.get(CONF_BRIGHTNESS_CURVES, {})
    )
    for entry in hass.config_entries.async_entries(DOMAIN):
        data = {**entry.data, **entry.options}
        programs.append(data)
        _merge_curves(curves, data.get(CONF_CURVES, {}))
        _merge_curves(brightness_curves, data.get(CONF_BRIGHTNESS_CURVES, {}))
    return {
        CONF_PROGRAMS: programs,
        CONF_CURVES: curves,
        CONF_BRIGHTNESS_CURVES: brightness_curves,
    }


async def save_config(hass: HomeAssistant, payload: dict[str, Any]) -> None:
    """Validate and synchronize the complete Studio config with HA entries."""
    payload = {
        CONF_PROGRAMS: payload[CONF_PROGRAMS],
        CONF_CURVES: payload.get(CONF_CURVES, {}),
        CONF_BRIGHTNESS_CURVES: payload.get(CONF_BRIGHTNESS_CURVES, {}),
    }
    try:
        parse_dim_to_warm_curves(payload[CONF_CURVES])
        parse_brightness_curves(payload[CONF_BRIGHTNESS_CURVES])
    except (TypeError, ValueError, KeyError) as err:
        raise vol.Invalid(str(err)) from err

    names: set[str] = set()
    cleaned_programs = []
    for program in payload[CONF_PROGRAMS]:
        if not isinstance(program, dict):
            raise vol.Invalid("Each program must be an object")
        try:
            # Reuse the integration's voluptuous program schema, including
            # required fields and Home Assistant entity ID validation.
            from . import PROGRAM_SCHEMA

            program = PROGRAM_SCHEMA(program)
        except vol.Invalid as err:
            raise vol.Invalid(str(err)) from err
        name = program.get(CONF_NAME)
        if not isinstance(name, str):
            raise vol.Invalid("Each program must have a name")
        name = name.strip().lower().replace(" ", "_")
        if not name or name in names:
            raise vol.Invalid("Program names must be unique")
        names.add(name)
        validated, errors = _validate_input({**program, CONF_NAME: name})
        if errors:
            raise vol.Invalid(f"Invalid program {name}: {', '.join(errors)}")
        validated[CONF_CURVES] = payload[CONF_CURVES]
        validated[CONF_BRIGHTNESS_CURVES] = payload[CONF_BRIGHTNESS_CURVES]
        cleaned_programs.append(validated)

    existing = {
        entry.data.get(CONF_NAME): entry
        for entry in hass.config_entries.async_entries(DOMAIN)
    }
    for program in cleaned_programs:
        name = program[CONF_NAME]
        entry = existing.pop(name, None)
        if entry is None:
            await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": "user"}, data=program
            )
        else:
            hass.config_entries.async_update_entry(entry, data=program, options={})
            await hass.config_entries.async_reload(entry.entry_id)
    for entry in existing.values():
        await hass.config_entries.async_remove(entry.entry_id)
    hass.data.setdefault(DOMAIN, {})["_studio_curves"] = {
        CONF_CURVES: payload[CONF_CURVES],
        CONF_BRIGHTNESS_CURVES: payload[CONF_BRIGHTNESS_CURVES],
    }
    if studio_store := hass.data[DOMAIN].get("_studio_store"):
        await studio_store.async_save(
            {
                CONF_CURVES: payload[CONF_CURVES],
                CONF_BRIGHTNESS_CURVES: payload[CONF_BRIGHTNESS_CURVES],
            }
        )


def async_register_websocket_commands(hass: HomeAssistant) -> None:
    """Register authenticated Studio configuration commands."""

    @websocket_api.websocket_command({"type": f"{DOMAIN}/config/get"})
    @websocket_api.require_admin
    @websocket_api.async_response
    async def ws_get_config(hass: HomeAssistant, connection: Any, msg: dict) -> None:
        connection.send_result(msg["id"], get_config(hass))

    @websocket_api.websocket_command(
        {
            "type": f"{DOMAIN}/config/save",
            vol.Required(CONF_PROGRAMS): list,
            vol.Optional(CONF_CURVES, default={}): dict,
            vol.Optional(CONF_BRIGHTNESS_CURVES, default={}): dict,
        }
    )
    @websocket_api.require_admin
    @websocket_api.async_response
    async def ws_save_config(hass: HomeAssistant, connection: Any, msg: dict) -> None:
        try:
            await save_config(hass, msg)
        except vol.Invalid as err:
            connection.send_error(msg["id"], "invalid_format", str(err))
            return
        connection.send_result(msg["id"], {"success": True})

    websocket_api.async_register_command(hass, ws_get_config)
    websocket_api.async_register_command(hass, ws_save_config)
