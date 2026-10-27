"""Constants for scheduled_scenes."""

from __future__ import annotations

DOMAIN = "scheduled_scenes"

CONF_PROGRAMS = "programs"
CONF_NAME = "name"
CONF_LIGHTS = "lights"
CONF_SCHEDULE = "schedule"
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

DEFAULT_TRANSITION_TIME = 120
DEFAULT_TRANSITION_INTERVAL = 120
DEFAULT_TRANSITION_TIME_ON_LIGHT_TURN_ON = 0.2
DEFAULT_TRANSITION_TIME_ON = 0.3
DEFAULT_DISABLE_WHEN_LIGHTS_OFF = True
DEFAULT_ENABLE_WHEN_LIGHT_TURN_ON = False
DEFAULT_ALLOW_TURN_ON_IF_ANY_ON = False

SERVICE_TURN_ON = "turn_on"
SERVICE_TURN_OFF = "turn_off"
SERVICE_ENABLE = "enable"
SERVICE_DISABLE = "disable"
SERVICE_RELOAD = "reload"

ATTR_TRANSITION = "transition"
ATTR_DURATION = "duration"
