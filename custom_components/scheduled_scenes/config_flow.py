"""Config flow and options flow for scheduled_scenes integration."""

from __future__ import annotations

import logging
from typing import Any
import yaml

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_ALLOW_TURN_ON_IF_ANY_ON,
    CONF_BRIGHTNESS_CURVES,
    CONF_CURVES,
    CONF_DISABLE_WHEN_LIGHTS_OFF,
    CONF_ENABLE_WHEN_LIGHT_TURN_ON,
    CONF_LIGHTS,
    CONF_NAME,
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
)
from .logic import (
    parse_brightness_curves,
    parse_dim_to_warm_curves,
    parse_schedule,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SCHEDULE_TEMPLATE = """- time: "05:00"
  brightness: 10
  temp: 2000
- time: "08:00"
  brightness: 100
  temp: 4000
- time: "14:00"
  brightness: 100
  temp: 5000
- time: "20:00"
  brightness: 60
  temp: 2500
- time: "23:00"
  brightness: 10
  temp: 2000
"""


def _get_schema(defaults: dict[str, Any], is_options: bool = False) -> vol.Schema:
    """Build form schema for config flow and options flow."""
    schedule_val = defaults.get(CONF_SCHEDULE, DEFAULT_SCHEDULE_TEMPLATE)
    if isinstance(schedule_val, list):
        schedule_val = yaml.dump(schedule_val, sort_keys=False)

    curves_val = defaults.get(CONF_CURVES, "")
    if isinstance(curves_val, (dict, list)):
        curves_val = yaml.dump(curves_val, sort_keys=False)

    b_curves_val = defaults.get(CONF_BRIGHTNESS_CURVES, "")
    if isinstance(b_curves_val, (dict, list)):
        b_curves_val = yaml.dump(b_curves_val, sort_keys=False)

    schema: dict[Any, Any] = {}
    if not is_options:
        schema[vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, ""))] = (
            TextSelector(TextSelectorConfig())
        )

    schema.update(
        {
            vol.Required(
                CONF_LIGHTS, default=defaults.get(CONF_LIGHTS, [])
            ): EntitySelector(
                EntitySelectorConfig(domain="light", multiple=True)
            ),
            vol.Required(
                CONF_TRANSITION_TIME,
                default=defaults.get(CONF_TRANSITION_TIME, DEFAULT_TRANSITION_TIME),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=3600,
                    step=1,
                    unit_of_measurement="s",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_TRANSITION_INTERVAL,
                default=defaults.get(
                    CONF_TRANSITION_INTERVAL, DEFAULT_TRANSITION_INTERVAL
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=3600,
                    step=1,
                    unit_of_measurement="s",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_TRANSITION_TIME_ON_LIGHT_TURN_ON,
                default=defaults.get(
                    CONF_TRANSITION_TIME_ON_LIGHT_TURN_ON,
                    DEFAULT_TRANSITION_TIME_ON_LIGHT_TURN_ON,
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0.0,
                    max=60.0,
                    step=0.1,
                    unit_of_measurement="s",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_TRANSITION_TIME_ON,
                default=defaults.get(
                    CONF_TRANSITION_TIME_ON, DEFAULT_TRANSITION_TIME_ON
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0.0,
                    max=60.0,
                    step=0.1,
                    unit_of_measurement="s",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_ENABLE_WHEN_LIGHT_TURN_ON,
                default=defaults.get(
                    CONF_ENABLE_WHEN_LIGHT_TURN_ON, DEFAULT_ENABLE_WHEN_LIGHT_TURN_ON
                ),
            ): BooleanSelector(),
            vol.Required(
                CONF_DISABLE_WHEN_LIGHTS_OFF,
                default=defaults.get(
                    CONF_DISABLE_WHEN_LIGHTS_OFF, DEFAULT_DISABLE_WHEN_LIGHTS_OFF
                ),
            ): BooleanSelector(),
            vol.Required(
                CONF_ALLOW_TURN_ON_IF_ANY_ON,
                default=defaults.get(
                    CONF_ALLOW_TURN_ON_IF_ANY_ON, DEFAULT_ALLOW_TURN_ON_IF_ANY_ON
                ),
            ): BooleanSelector(),
            vol.Required(
                CONF_SCHEDULE, default=schedule_val
            ): TextSelector(TextSelectorConfig(multiline=True)),
            vol.Optional(
                CONF_CURVES, default=curves_val
            ): TextSelector(TextSelectorConfig(multiline=True)),
            vol.Optional(
                CONF_BRIGHTNESS_CURVES, default=b_curves_val
            ): TextSelector(TextSelectorConfig(multiline=True)),
        }
    )
    return vol.Schema(schema)


def _validate_input(user_input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate user input and parse YAML schedule and curves."""
    errors: dict[str, str] = {}
    cleaned = dict(user_input)

    schedule_raw = user_input.get(CONF_SCHEDULE, "")
    if isinstance(schedule_raw, str):
        try:
            parsed_yaml = yaml.safe_load(schedule_raw)
            if not isinstance(parsed_yaml, list) or len(parsed_yaml) == 0:
                errors[CONF_SCHEDULE] = "invalid_schedule"
            else:
                steps = parse_schedule(parsed_yaml)
                if not steps:
                    errors[CONF_SCHEDULE] = "invalid_schedule"
                else:
                    cleaned[CONF_SCHEDULE] = parsed_yaml
        except Exception:
            errors[CONF_SCHEDULE] = "invalid_schedule"
    elif isinstance(schedule_raw, list):
        steps = parse_schedule(schedule_raw)
        if not steps:
            errors[CONF_SCHEDULE] = "invalid_schedule"

    curves_raw = user_input.get(CONF_CURVES)
    if isinstance(curves_raw, str):
        curves_str = curves_raw.strip()
        if curves_str:
            try:
                parsed_curves = yaml.safe_load(curves_str)
                if parsed_curves:
                    parse_dim_to_warm_curves(parsed_curves)
                    cleaned[CONF_CURVES] = parsed_curves
                else:
                    cleaned.pop(CONF_CURVES, None)
            except Exception:
                errors[CONF_CURVES] = "invalid_curves"
        else:
            cleaned.pop(CONF_CURVES, None)
    elif isinstance(curves_raw, (dict, list)):
        try:
            parse_dim_to_warm_curves(curves_raw)
            cleaned[CONF_CURVES] = curves_raw
        except Exception:
            errors[CONF_CURVES] = "invalid_curves"

    b_curves_raw = user_input.get(CONF_BRIGHTNESS_CURVES)
    if isinstance(b_curves_raw, str):
        b_curves_str = b_curves_raw.strip()
        if b_curves_str:
            try:
                parsed_b_curves = yaml.safe_load(b_curves_str)
                if parsed_b_curves:
                    parse_brightness_curves(parsed_b_curves)
                    cleaned[CONF_BRIGHTNESS_CURVES] = parsed_b_curves
                else:
                    cleaned.pop(CONF_BRIGHTNESS_CURVES, None)
            except Exception:
                errors[CONF_BRIGHTNESS_CURVES] = "invalid_brightness_curves"
        else:
            cleaned.pop(CONF_BRIGHTNESS_CURVES, None)
    elif isinstance(b_curves_raw, (dict, list)):
        try:
            parse_brightness_curves(b_curves_raw)
            cleaned[CONF_BRIGHTNESS_CURVES] = b_curves_raw
        except Exception:
            errors[CONF_BRIGHTNESS_CURVES] = "invalid_brightness_curves"

    return cleaned, errors


class ScheduledScenesConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for scheduled_scenes."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            name = str(user_input.get(CONF_NAME, "")).strip().lower().replace(" ", "_")
            user_input[CONF_NAME] = name

            # Check if name is already registered
            for entry in self._async_current_entries():
                if entry.data.get(CONF_NAME) == name:
                    return self.async_abort(reason="already_configured")

            cleaned, errors = _validate_input(user_input)
            if not errors:
                return self.async_create_entry(
                    title=name.title(),
                    data=cleaned,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_get_schema(user_input or {}),
            errors=errors,
        )

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle import from YAML configuration."""
        name = str(import_data.get(CONF_NAME, "")).strip().lower().replace(" ", "_")
        import_data[CONF_NAME] = name

        for entry in self._async_current_entries():
            if entry.data.get(CONF_NAME) == name:
                self.hass.config_entries.async_update_entry(entry, data=import_data)
                return self.async_abort(reason="already_configured")

        cleaned, errors = _validate_input(import_data)
        if errors:
            return self.async_abort(reason="invalid_schedule")

        return self.async_create_entry(
            title=name.title(),
            data=cleaned,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get options flow handler."""
        return ScheduledScenesOptionsFlow(config_entry)


class ScheduledScenesOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for scheduled_scenes."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        defaults = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            cleaned, errors = _validate_input(user_input)
            if not errors:
                return self.async_create_entry(title="", data=cleaned)

        return self.async_show_form(
            step_id="init",
            data_schema=_get_schema(user_input or defaults, is_options=True),
            errors=errors,
        )
