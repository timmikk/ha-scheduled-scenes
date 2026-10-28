"""Constants for scheduled_scenes."""

from __future__ import annotations

DOMAIN = "scheduled_scenes"

CONF_PROGRAMS = "programs"
CONF_NAME = "name"
CONF_LIGHTS = "lights"
CONF_SCHEDULE = "schedule"
CONF_CURVES = "curves"
CONF_CURVE = "curve"
CONF_BRIGHTNESS_CURVES = "brightness_curves"
CONF_BRIGHTNESS_CURVE = "brightness_curve"
CONF_POINTS = "points"
CONF_DIM_TO_WARM = "dim_to_warm"
CONF_DIMM_TO_WARM = "dimm_to_warm"
CONF_TRANSITION_TIME = "transition_time"
CONF_TRANSITION_INTERVAL = "transition_interval"
CONF_BRIGHTNESS = "brightness"
CONF_COLOR_TEMP = "temp"
CONF_TIME = "time"
CONF_DISABLE_WHEN_LIGHTS_OFF = "disable_when_lights_off"
CONF_TRANSITION_TIME_ON_LIGHT_TURN_ON = "transition_time_light_on_trigger"
CONF_TRANSITION_TIME_ON = "transition_time_light_on"
CONF_ALLOW_TURN_ON_IF_ANY_ON = "allow_turn_on_if_any_on"
CONF_ENABLE_WHEN_LIGHT_TURN_ON = "enable_when_light_turn_on"
CONF_MANUAL_OVERRIDE_TIMEOUT = "manual_override_timeout"

DEFAULT_TRANSITION_TIME = 120
DEFAULT_TRANSITION_INTERVAL = 120
DEFAULT_TRANSITION_TIME_ON_LIGHT_TURN_ON = 0.2
DEFAULT_TRANSITION_TIME_ON = 0.3
DEFAULT_DISABLE_WHEN_LIGHTS_OFF = True
DEFAULT_ENABLE_WHEN_LIGHT_TURN_ON = False
DEFAULT_ALLOW_TURN_ON_IF_ANY_ON = False
DEFAULT_COLOR_TEMP = 2700
DEFAULT_MANUAL_OVERRIDE_TIMEOUT = 0

SERVICE_TURN_ON = "turn_on"
SERVICE_TURN_OFF = "turn_off"
SERVICE_ENABLE = "enable"
SERVICE_DISABLE = "disable"
SERVICE_RELOAD = "reload"
SERVICE_ADJUST_BRIGHTNESS = "adjust_brightness"
SERVICE_STEP_BRIGHTNESS = "step_brightness"
SERVICE_RESUME_SCHEDULE = "resume_schedule"

ATTR_TRANSITION = "transition"
ATTR_DURATION = "duration"
ATTR_STEP = "step"
ATTR_BRIGHTNESS = "brightness"
ATTR_BRIGHTNESS_PCT = "brightness_pct"
