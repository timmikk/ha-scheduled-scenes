"""Runtime manager and coordinator for scheduled_scenes programs."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
import homeassistant.util.dt as dt_util

from .const import (
    CONF_ALLOW_TURN_ON_IF_ANY_ON,
    CONF_BRIGHTNESS_CURVES,
    CONF_CURVES,
    CONF_DISABLE_WHEN_LIGHTS_OFF,
    CONF_ENABLE_WHEN_LIGHT_TURN_ON,
    CONF_LIGHTS,
    CONF_MANUAL_OVERRIDE_TIMEOUT,
    CONF_NAME,
    CONF_SCHEDULE,
    CONF_TRANSITION_INTERVAL,
    CONF_TRANSITION_TIME,
    CONF_TRANSITION_TIME_ON,
    CONF_TRANSITION_TIME_ON_LIGHT_TURN_ON,
    DEFAULT_ALLOW_TURN_ON_IF_ANY_ON,
    DEFAULT_DISABLE_WHEN_LIGHTS_OFF,
    DEFAULT_ENABLE_WHEN_LIGHT_TURN_ON,
    DEFAULT_MANUAL_OVERRIDE_TIMEOUT,
    DEFAULT_TRANSITION_INTERVAL,
    DEFAULT_TRANSITION_TIME,
    DEFAULT_TRANSITION_TIME_ON,
    DEFAULT_TRANSITION_TIME_ON_LIGHT_TURN_ON,
)
from .logic import (
    ActiveTransition,
    BrightnessCurve,
    DimToWarmCurve,
    ScheduleStep,
    calculate_light_state,
    calculate_manual_light_state,
    calculate_transition_seconds,
    estimate_room_brightness,
    parse_brightness_curves,
    parse_dim_to_warm_curves,
    parse_schedule,
    resolve_active_transition,
)

_LOGGER = logging.getLogger(__name__)


class ScheduledSceneProgram:
    """Manages scheduling, triggers, and state for a single room/program."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize program from config."""
        self.hass = hass
        self.config = config

        self.name: str = config.get(CONF_NAME, "")
        self.lights: list[str] = list(config.get(CONF_LIGHTS, []))
        self.transition_time: float = float(config.get(CONF_TRANSITION_TIME, DEFAULT_TRANSITION_TIME))
        self.transition_interval: float = float(
            config.get(CONF_TRANSITION_INTERVAL, DEFAULT_TRANSITION_INTERVAL)
        )
        self.transition_time_light_on_trigger: float = float(
            config.get(
                CONF_TRANSITION_TIME_ON_LIGHT_TURN_ON,
                DEFAULT_TRANSITION_TIME_ON_LIGHT_TURN_ON,
            )
        )
        self.transition_time_on: float = float(
            config.get(CONF_TRANSITION_TIME_ON, DEFAULT_TRANSITION_TIME_ON)
        )
        self.enable_when_light_turn_on: bool = bool(
            config.get(CONF_ENABLE_WHEN_LIGHT_TURN_ON, DEFAULT_ENABLE_WHEN_LIGHT_TURN_ON)
        )
        self.disable_when_lights_off: bool = bool(
            config.get(CONF_DISABLE_WHEN_LIGHTS_OFF, DEFAULT_DISABLE_WHEN_LIGHTS_OFF)
        )
        self.allow_turn_on_if_any_on: bool = bool(
            config.get(CONF_ALLOW_TURN_ON_IF_ANY_ON, DEFAULT_ALLOW_TURN_ON_IF_ANY_ON)
        )
        self.manual_override_timeout: float = float(
            config.get(CONF_MANUAL_OVERRIDE_TIMEOUT, DEFAULT_MANUAL_OVERRIDE_TIMEOUT)
        )

        self.curves: dict[str, DimToWarmCurve]
        self.light_curves: dict[str, DimToWarmCurve]
        self.curves, self.light_curves = parse_dim_to_warm_curves(config.get(CONF_CURVES))

        self.brightness_curves: dict[str, BrightnessCurve]
        self.light_brightness_curves: dict[str, BrightnessCurve]
        self.brightness_curves, self.light_brightness_curves = parse_brightness_curves(
            config.get(CONF_BRIGHTNESS_CURVES)
        )

        self.schedule: list[ScheduleStep] = parse_schedule(config.get(CONF_SCHEDULE, []))

        self.enabled: bool = True
        self.manual_brightness: int | None = None
        self.current_transition: ActiveTransition | None = None
        self._listeners: list[Callable[[], None]] = []

        self._unsub_interval: CALLBACK_TYPE | None = None
        self._unsub_state_change: CALLBACK_TYPE | None = None
        self._unsub_disable_timer: CALLBACK_TYPE | None = None
        self._unsub_override_timer: CALLBACK_TYPE | None = None

    @callback
    def async_add_listener(self, update_callback: Callable[[], None]) -> CALLBACK_TYPE:
        """Register entity callback to be notified on state changes."""
        self._listeners.append(update_callback)

        def remove_listener() -> None:
            self._listeners.remove(update_callback)

        return remove_listener

    def _notify_listeners(self) -> None:
        """Notify registered entity listeners."""
        for update_callback in self._listeners:
            update_callback()

    async def async_start(self) -> None:
        """Start listening to state changes and periodic interval timers."""
        now = dt_util.now()
        self.current_transition = resolve_active_transition(self.schedule, now)

        self._unsub_interval = async_track_time_interval(
            self.hass,
            self._async_periodic_callback,
            timedelta(seconds=self.transition_interval),
            cancel_on_shutdown=True,
        )

        if self.lights:
            self._unsub_state_change = async_track_state_change_event(
                self.hass,
                self.lights,
                self._async_light_state_change,
            )

        _LOGGER.debug(
            "Program [%s] started: interval=%ss, lights=%s, curves=%s, brightness_curves=%s",
            self.name,
            self.transition_interval,
            self.lights,
            list(self.curves.keys()),
            list(self.brightness_curves.keys()),
        )

    async def async_stop(self) -> None:
        """Unsubscribe all listeners and cancel timers."""
        if self._unsub_interval:
            self._unsub_interval()
            self._unsub_interval = None

        if self._unsub_state_change:
            self._unsub_state_change()
            self._unsub_state_change = None

        if self._unsub_disable_timer:
            self._unsub_disable_timer()
            self._unsub_disable_timer = None

        if self._unsub_override_timer:
            self._unsub_override_timer()
            self._unsub_override_timer = None

    def is_any_light_on(self) -> bool:
        """Check if any light entity in the program is currently on."""
        for entity_id in self.lights:
            state = self.hass.states.get(entity_id)
            if state is not None and state.state == "on":
                return True
        return False

    async def _async_light_state_change(self, event: Event) -> None:
        """Handle light state change event."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        val = new_state.state
        if val == "on":
            if self.enable_when_light_turn_on:
                if self.allow_turn_on_if_any_on:
                    await self.async_turn_on()
                else:
                    self.set_enabled(True)
                    await self.async_transition(
                        transition_time_override=self.transition_time_light_on_trigger
                    )
        elif val in ("off", "unavailable"):
            if not self.is_any_light_on():
                self.manual_brightness = None
                if self._unsub_override_timer:
                    self._unsub_override_timer()
                    self._unsub_override_timer = None
                if self.disable_when_lights_off:
                    self.set_enabled(False)

    async def _async_periodic_callback(self, now: datetime) -> None:
        """Periodic timer callback."""
        if self.enabled and self.manual_brightness is None:
            await self.async_transition()

    async def async_transition(
        self,
        transition_time_override: float | None = None,
        allow_turn_lights_on: bool | None = None,
    ) -> None:
        """Calculate and dispatch light transitions."""
        if not self.enabled:
            return

        now = dt_util.now()
        transition = resolve_active_transition(self.schedule, now)
        if transition is None:
            return

        self.current_transition = transition

        if allow_turn_lights_on is None:
            allow_turn_lights_on = self.allow_turn_on_if_any_on and self.is_any_light_on()

        transition_seconds = calculate_transition_seconds(
            transition,
            transition_time_override,
            self.transition_time,
            now,
        )

        for light_id in self.lights:
            state = self.hass.states.get(light_id)
            light_is_on = state is not None and state.state == "on"

            if allow_turn_lights_on or light_is_on:
                b, temp = calculate_light_state(
                    transition,
                    light_id,
                    self.light_curves,
                    self.light_brightness_curves,
                )
                curve_info = self.light_curves.get(light_id)
                _LOGGER.debug(
                    "Program [%s] light [%s] target: brightness=%s%%, temp=%sK (curve=%s)",
                    self.name,
                    light_id,
                    b,
                    temp,
                    curve_info.name if curve_info else None,
                )
                await self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {
                        "entity_id": light_id,
                        "brightness_pct": b,
                        "color_temp_kelvin": temp,
                        "transition": transition_seconds,
                    },
                    blocking=False,
                )

        self._notify_listeners()

    async def async_adjust_brightness(
        self,
        step: int | None = None,
        brightness: int | None = None,
        transition: float | None = None,
    ) -> None:
        """Adjust or set room brightness, pausing automatic schedule transitions."""
        if step is None and brightness is None:
            step = 10

        if brightness is not None:
            target_b = max(0, min(100, int(brightness)))
        else:
            if self.manual_brightness is not None:
                baseline = self.manual_brightness
            else:
                current_states: dict[str, int] = {}
                for light_id in self.lights:
                    st = self.hass.states.get(light_id)
                    if st is not None and st.state == "on":
                        raw_b = st.attributes.get("brightness")
                        if raw_b is not None:
                            current_states[light_id] = round((int(raw_b) / 255) * 100)
                        else:
                            current_states[light_id] = 100

                if not current_states:
                    baseline = 0
                else:
                    baseline = estimate_room_brightness(
                        current_states, self.light_brightness_curves
                    )

            target_b = max(0, min(100, baseline + int(step)))

        self.manual_brightness = target_b

        if self._unsub_override_timer:
            self._unsub_override_timer()
            self._unsub_override_timer = None

        if self.manual_override_timeout > 0:
            @callback
            def _auto_resume(_now: datetime) -> None:
                self.hass.async_create_task(self.async_resume_schedule())

            self._unsub_override_timer = async_call_later(
                self.hass,
                self.manual_override_timeout * 60,
                _auto_resume,
            )

        t_time = transition if transition is not None else self.transition_time_on

        if target_b == 0:
            if self.lights:
                await self.hass.services.async_call(
                    "light",
                    "turn_off",
                    {"entity_id": self.lights, "transition": t_time},
                    blocking=False,
                )
        else:
            for light_id in self.lights:
                light_b, light_temp = calculate_manual_light_state(
                    target_b,
                    light_id,
                    self.light_brightness_curves,
                    self.light_curves,
                )
                if light_b <= 0:
                    await self.hass.services.async_call(
                        "light",
                        "turn_off",
                        {"entity_id": light_id, "transition": t_time},
                        blocking=False,
                    )
                else:
                    await self.hass.services.async_call(
                        "light",
                        "turn_on",
                        {
                            "entity_id": light_id,
                            "brightness_pct": light_b,
                            "color_temp_kelvin": light_temp,
                            "transition": t_time,
                        },
                        blocking=False,
                    )

        self._notify_listeners()

    async def async_resume_schedule(self, transition_time: float | None = None) -> None:
        """Clear manual brightness override and resume automatic schedule transitions."""
        if self._unsub_override_timer:
            self._unsub_override_timer()
            self._unsub_override_timer = None

        self.manual_brightness = None
        t_time = transition_time if transition_time is not None else self.transition_time_on
        if self.enabled:
            await self.async_transition(transition_time_override=t_time)
        self._notify_listeners()

    async def async_turn_on(self, transition_time: float | None = None) -> None:
        """Turn on all program lights with current schedule parameters."""
        self.manual_brightness = None
        if self._unsub_override_timer:
            self._unsub_override_timer()
            self._unsub_override_timer = None
        self.set_enabled(True)
        t_time = transition_time if transition_time is not None else self.transition_time_on
        await self.async_transition(transition_time_override=t_time, allow_turn_lights_on=True)

    async def async_turn_off(self, transition_time: float | None = None) -> None:
        """Turn off all lights in the program and disable the schedule."""
        self.manual_brightness = None
        if self._unsub_override_timer:
            self._unsub_override_timer()
            self._unsub_override_timer = None
        self.set_enabled(False)
        t_time = transition_time if transition_time is not None else self.transition_time_on
        if self.lights:
            await self.hass.services.async_call(
                "light",
                "turn_off",
                {"entity_id": self.lights, "transition": t_time},
                blocking=False,
            )
        self._notify_listeners()

    def set_enabled(self, enabled: bool, duration: int = 0) -> None:
        """Enable or disable the program, with optional auto-enable timer."""
        if self._unsub_disable_timer:
            self._unsub_disable_timer()
            self._unsub_disable_timer = None

        if enabled:
            self.manual_brightness = None
            if self._unsub_override_timer:
                self._unsub_override_timer()
                self._unsub_override_timer = None

        self.enabled = enabled

        if not enabled and duration > 0:
            @callback
            def _auto_enable(_now: datetime) -> None:
                self.set_enabled(True)

            self._unsub_disable_timer = async_call_later(
                self.hass,
                duration * 60,
                _auto_enable,
            )

        self._notify_listeners()
