"""Pure mathematical schedule and curve interpolation logic for scheduled_scenes.

This module contains zero Home Assistant runtime dependencies, enabling
100% testability with pytest without HA runtime fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
import logging

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class LightOverride:
    """Per-light brightness or color temperature override at a schedule step."""

    brightness: int | None = None
    temp: int | None = None


@dataclass(frozen=True)
class ScheduleStep:
    """A single scheduled checkpoint defining target light parameters at a given time."""

    time: time
    brightness: int
    temp: int
    lights: dict[str, LightOverride] = field(default_factory=dict)


@dataclass(frozen=True)
class ActiveTransition:
    """The resolved active transition interval between two schedule steps."""

    start_step: ScheduleStep
    end_step: ScheduleStep
    start_dt: datetime
    end_dt: datetime
    total_seconds: float
    seconds_from_start: float


def parse_time(time_val: str | time) -> time:
    """Parse time string 'HH:MM' or 'HH:MM:SS' into a datetime.time object."""
    if isinstance(time_val, time):
        return time_val
    time_str = str(time_val).strip()
    try:
        return time.fromisoformat(time_str)
    except ValueError:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        second = int(parts[2]) if len(parts) > 2 else 0
        return time(hour=hour, minute=minute, second=second)


def parse_schedule_step(data: dict) -> ScheduleStep:
    """Parse a single raw schedule step dictionary into a ScheduleStep."""
    t = parse_time(data["time"])
    brightness = int(data.get("brightness", 100))
    temp = int(data.get("temp", 4000))

    light_overrides: dict[str, LightOverride] = {}
    if "lights" in data and isinstance(data["lights"], dict):
        for light_id, props in data["lights"].items():
            if isinstance(props, dict):
                b = int(props["brightness"]) if "brightness" in props else None
                k = int(props["temp"]) if "temp" in props else None
                light_overrides[light_id] = LightOverride(brightness=b, temp=k)

    return ScheduleStep(
        time=t,
        brightness=brightness,
        temp=temp,
        lights=light_overrides,
    )


def parse_schedule(raw_steps: list[dict]) -> list[ScheduleStep]:
    """Parse a list of raw step dictionaries into sorted ScheduleStep instances."""
    if not raw_steps:
        return []
    steps = [parse_schedule_step(s) for s in raw_steps]
    # Filter duplicate times keeping later ones, and ensure sorted order
    steps.sort(key=lambda s: s.time)
    return steps


def resolve_active_transition(
    steps: list[ScheduleStep],
    now: datetime,
) -> ActiveTransition | None:
    """Resolve which transition is ongoing for the given time."""
    if not steps:
        return None

    tz = now.tzinfo
    if tz is not None:
        now = now.replace(tzinfo=None)

    if len(steps) == 1:
        # Single step: constant brightness and temp 24/7
        step = steps[0]
        start_dt = datetime.combine(now.date(), step.time)
        end_dt = start_dt + timedelta(days=1)
        if tz is not None:
            start_dt = start_dt.replace(tzinfo=tz)
            end_dt = end_dt.replace(tzinfo=tz)
        return ActiveTransition(
            start_step=step,
            end_step=step,
            start_dt=start_dt,
            end_dt=end_dt,
            total_seconds=86400.0,
            seconds_from_start=max(0.0, (now - start_dt.replace(tzinfo=None)).total_seconds()),
        )

    # Find where 'now' falls among sorted steps
    today = now.date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    # Construct datetime intervals spanning yesterday, today, and tomorrow
    all_step_dts: list[tuple[datetime, ScheduleStep]] = []
    for d in (yesterday, today, tomorrow):
        for s in steps:
            all_step_dts.append((datetime.combine(d, s.time), s))

    # Search for interval where start_dt <= now < end_dt
    for i in range(len(all_step_dts) - 1):
        start_dt, start_step = all_step_dts[i]
        end_dt, end_step = all_step_dts[i + 1]

        # Ignore invalid zero or negative transitions
        if end_dt <= start_dt:
            continue

        if start_dt <= now < end_dt:
            total_seconds = (end_dt - start_dt).total_seconds()
            seconds_from_start = (now - start_dt).total_seconds()
            if tz is not None:
                start_dt = start_dt.replace(tzinfo=tz)
                end_dt = end_dt.replace(tzinfo=tz)
            return ActiveTransition(
                start_step=start_step,
                end_step=end_step,
                start_dt=start_dt,
                end_dt=end_dt,
                total_seconds=total_seconds,
                seconds_from_start=seconds_from_start,
            )

    return None


def get_step_value(step: ScheduleStep, light_id: str, prop: str) -> int:
    """Extract property value (brightness or temp) with per-light override."""
    if light_id in step.lights:
        override = step.lights[light_id]
        if prop == "brightness" and override.brightness is not None:
            return override.brightness
        if prop == "temp" and override.temp is not None:
            return override.temp

    if prop == "brightness":
        return step.brightness
    return step.temp


def interpolate_scalar(start_val: int, end_val: int, fraction: float) -> int:
    """Linearly interpolate between start_val and end_val at fraction in [0, 1]."""
    clamped_fraction = max(0.0, min(1.0, fraction))
    val = round(start_val + (end_val - start_val) * clamped_fraction)
    if start_val <= end_val:
        return max(start_val, min(end_val, val))
    return max(end_val, min(start_val, val))


def calculate_light_state(
    transition: ActiveTransition,
    light_id: str,
) -> tuple[int, int]:
    """Calculate target (brightness_pct, color_temp_kelvin) for a light in transition."""
    if transition.total_seconds <= 0:
        fraction = 0.0
    else:
        fraction = transition.seconds_from_start / transition.total_seconds

    b_start = get_step_value(transition.start_step, light_id, "brightness")
    b_end = get_step_value(transition.end_step, light_id, "brightness")
    brightness = interpolate_scalar(b_start, b_end, fraction)

    t_start = get_step_value(transition.start_step, light_id, "temp")
    t_end = get_step_value(transition.end_step, light_id, "temp")
    temp = interpolate_scalar(t_start, t_end, fraction)

    return brightness, temp


def calculate_transition_seconds(
    transition: ActiveTransition | None,
    override_seconds: float | None,
    configured_seconds: float,
    now: datetime,
) -> float:
    """Calculate the transition time to send to light.turn_on."""
    if override_seconds is not None:
        return float(override_seconds)

    if transition is None:
        return float(configured_seconds)

    seconds_from_start = (now - transition.start_dt).total_seconds()
    return float(min(seconds_from_start, configured_seconds))
