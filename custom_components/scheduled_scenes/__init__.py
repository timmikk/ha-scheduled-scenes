"""Scheduled scenes custom component for Home Assistant."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.reload import async_integration_yaml_config

from .const import (
    ATTR_DURATION,
    ATTR_TRANSITION,
    CONF_ALLOW_TURN_ON_IF_ANY_ON,
    CONF_CURVES,
    CONF_DISABLE_WHEN_LIGHTS_OFF,
    CONF_ENABLE_WHEN_LIGHT_TURN_ON,
    CONF_LIGHTS,
    CONF_NAME,
    CONF_PROGRAMS,
    CONF_SCHEDULE,
    CONF_TRANSITION_INTERVAL,
    CONF_TRANSITION_TIME,
    CONF_TRANSITION_TIME_ON,
    CONF_TRANSITION_TIME_ON_LIGHT_TURN_ON,
    DEFAULT_ALLOW_TURN_ON_IF_ANY_ON,
    DEFAULT_DISABLE_WHEN_LIGHTS_OFF,
    DEFAULT_ENABLE_WHEN_LIGHT_TURN_ON,
    DEFAULT_TRANSITION_INTERVAL,
    DEFAULT_TRANSITION_TIME,
    DEFAULT_TRANSITION_TIME_ON,
    DEFAULT_TRANSITION_TIME_ON_LIGHT_TURN_ON,
    DOMAIN,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_RELOAD,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from .coordinator import ScheduledSceneProgram

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.SENSOR]

CURVES_SCHEMA = vol.Any(
    dict,
    vol.All(cv.ensure_list, [dict]),
)

PROGRAM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_LIGHTS): cv.entity_ids,
        vol.Optional(CONF_TRANSITION_TIME, default=DEFAULT_TRANSITION_TIME): vol.Coerce(float),
        vol.Optional(
            CONF_TRANSITION_INTERVAL, default=DEFAULT_TRANSITION_INTERVAL
        ): vol.Coerce(float),
        vol.Optional(
            CONF_TRANSITION_TIME_ON_LIGHT_TURN_ON,
            default=DEFAULT_TRANSITION_TIME_ON_LIGHT_TURN_ON,
        ): vol.Coerce(float),
        vol.Optional(
            CONF_TRANSITION_TIME_ON, default=DEFAULT_TRANSITION_TIME_ON
        ): vol.Coerce(float),
        vol.Optional(
            CONF_ENABLE_WHEN_LIGHT_TURN_ON, default=DEFAULT_ENABLE_WHEN_LIGHT_TURN_ON
        ): cv.boolean,
        vol.Optional(
            CONF_DISABLE_WHEN_LIGHTS_OFF, default=DEFAULT_DISABLE_WHEN_LIGHTS_OFF
        ): cv.boolean,
        vol.Optional(
            CONF_ALLOW_TURN_ON_IF_ANY_ON, default=DEFAULT_ALLOW_TURN_ON_IF_ANY_ON
        ): cv.boolean,
        vol.Optional(CONF_CURVES): CURVES_SCHEMA,
        vol.Required(CONF_SCHEDULE): vol.All(cv.ensure_list, [dict]),
    }
)

PROGRAMS_LIST_SCHEMA = vol.All(cv.ensure_list, [PROGRAM_SCHEMA])

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Any(
            PROGRAMS_LIST_SCHEMA,
            vol.Schema(
                {
                    vol.Optional(CONF_CURVES): CURVES_SCHEMA,
                    vol.Optional(CONF_PROGRAMS): PROGRAMS_LIST_SCHEMA,
                    vol.Optional("rooms"): PROGRAMS_LIST_SCHEMA,
                },
                extra=vol.ALLOW_EXTRA,
            ),
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def _resolve_programs_and_curves(
    domain_conf: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Extract global curves and program configs from domain configuration."""
    global_curves: dict[str, Any] = {}
    programs: list[dict[str, Any]] = []

    if isinstance(domain_conf, list):
        programs = domain_conf
    elif isinstance(domain_conf, dict):
        curves = domain_conf.get(CONF_CURVES)
        if isinstance(curves, (dict, list)):
            global_curves = curves
        programs = domain_conf.get(CONF_PROGRAMS, domain_conf.get("rooms", []))

    resolved_programs: list[dict[str, Any]] = []
    for prog_conf in programs:
        data = dict(prog_conf)
        if global_curves:
            if CONF_CURVES not in data:
                data[CONF_CURVES] = global_curves
            elif isinstance(data[CONF_CURVES], dict) and isinstance(global_curves, dict):
                data[CONF_CURVES] = {**global_curves, **data[CONF_CURVES]}
        resolved_programs.append(data)

    return global_curves, resolved_programs


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up scheduled_scenes from YAML."""
    hass.data.setdefault(DOMAIN, {})

    _register_services(hass)

    if DOMAIN in config:
        _, programs = _resolve_programs_and_curves(config[DOMAIN])
        for prog_conf in programs:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_IMPORT},
                    data=prog_conf,
                )
            )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up scheduled_scenes from a config entry."""
    entry_data = {**entry.data, **entry.options}
    program = ScheduledSceneProgram(hass, entry_data)
    await program.async_start()

    hass.data[DOMAIN][entry.entry_id] = program

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register legacy compatibility aliases per program
    _register_program_aliases(hass, program)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry after options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        program: ScheduledSceneProgram = hass.data[DOMAIN].pop(entry.entry_id)
        await program.async_stop()
        _unregister_program_aliases(hass, program)
    return unload_ok


def _get_programs(hass: HomeAssistant, call: ServiceCall) -> list[ScheduledSceneProgram]:
    """Resolve target programs from service call target or all entries."""
    store = hass.data.get(DOMAIN, {})
    programs: list[ScheduledSceneProgram] = [\
        p for k, p in store.items() if isinstance(p, ScheduledSceneProgram)\
    ]

    target_entities = call.data.get("entity_id")
    if not target_entities:
        return programs

    if isinstance(target_entities, str):
        target_entities = [target_entities]

    matched: list[ScheduledSceneProgram] = []
    for prog in programs:
        expected_switch = f"switch.schedule_{prog.name}"
        expected_short = f"switch.{prog.name}"
        if any(
            e in target_entities or prog.name in e
            for e in (expected_switch, expected_short, *target_entities)
        ):
            matched.append(prog)

    return matched or programs


def _register_services(hass: HomeAssistant) -> None:
    """Register domain-level services."""
    if hass.services.has_service(DOMAIN, SERVICE_TURN_ON):
        return

    async def _handle_turn_on(call: ServiceCall) -> None:
        transition = call.data.get(ATTR_TRANSITION)
        for prog in _get_programs(hass, call):
            await prog.async_turn_on(transition_time=transition)

    async def _handle_turn_off(call: ServiceCall) -> None:
        transition = call.data.get(ATTR_TRANSITION)
        for prog in _get_programs(hass, call):
            await prog.async_turn_off(transition_time=transition)

    async def _handle_enable(call: ServiceCall) -> None:
        for prog in _get_programs(hass, call):
            prog.set_enabled(True)

    async def _handle_disable(call: ServiceCall) -> None:
        duration = int(call.data.get(ATTR_DURATION, 0))
        for prog in _get_programs(hass, call):
            prog.set_enabled(False, duration=duration)

    async def _handle_reload(_call: ServiceCall) -> None:
        conf = await async_integration_yaml_config(hass, DOMAIN)
        if conf and DOMAIN in conf:
            _, programs = _resolve_programs_and_curves(conf[DOMAIN])
            for prog_conf in programs:
                await hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": SOURCE_IMPORT},
                    data=prog_conf,
                )

    hass.services.async_register(DOMAIN, SERVICE_TURN_ON, _handle_turn_on)
    hass.services.async_register(DOMAIN, SERVICE_TURN_OFF, _handle_turn_off)
    hass.services.async_register(DOMAIN, SERVICE_ENABLE, _handle_enable)
    hass.services.async_register(DOMAIN, SERVICE_DISABLE, _handle_disable)
    hass.services.async_register(DOMAIN, SERVICE_RELOAD, _handle_reload)


def _register_program_aliases(hass: HomeAssistant, program: ScheduledSceneProgram) -> None:
    """Register legacy service aliases for a program."""
    name = program.name
    if not name:
        return

    async def _alias_turn_on(call: ServiceCall) -> None:
        await program.async_turn_on(transition_time=call.data.get(ATTR_TRANSITION))

    async def _alias_turn_off(call: ServiceCall) -> None:
        await program.async_turn_off(transition_time=call.data.get(ATTR_TRANSITION))

    async def _alias_enable(_call: ServiceCall) -> None:
        program.set_enabled(True)

    async def _alias_disable(call: ServiceCall) -> None:
        program.set_enabled(False, duration=int(call.data.get(ATTR_DURATION, 0)))

    hass.services.async_register(DOMAIN, f"{name}_turn_on", _alias_turn_on)
    hass.services.async_register(DOMAIN, f"{name}_turn_off", _alias_turn_off)
    hass.services.async_register(DOMAIN, f"{name}_enable", _alias_enable)
    hass.services.async_register(DOMAIN, f"{name}_disable", _alias_disable)


def _unregister_program_aliases(hass: HomeAssistant, program: ScheduledSceneProgram) -> None:
    """Unregister legacy service aliases for a program."""
    name = program.name
    if not name:
        return

    hass.services.async_remove(DOMAIN, f"{name}_turn_on")
    hass.services.async_remove(DOMAIN, f"{name}_turn_off")
    hass.services.async_remove(DOMAIN, f"{name}_enable")
    hass.services.async_remove(DOMAIN, f"{name}_disable")
