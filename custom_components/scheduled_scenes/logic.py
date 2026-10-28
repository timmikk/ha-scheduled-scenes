"""Pure mathematical schedule and curve interpolation logic for scheduled_scenes.

This module contains zero Home Assistant runtime dependencies, enabling
100% testability with pytest without HA runtime fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

DEFAULT_COLOR_TEMP = 2700


@dataclass(frozen=True)
class LightOverride:
    """Per-light brightness or color temperature override at a schedule step."""

    brightness: int | None = None
    temp: int | None = None


@dataclass(frozen=True)
class DimToWarmPoint:
    """A single coordinate point on a dim-to-warm curve."""

    brightness: int
    temp: int


@dataclass(frozen=True)
class DimToWarmCurve:
    """A dim-to-warm curve mapping brightness percentages to color temperature in Kelvin."""

    name: str
    lights: list[str] = field(default_factory=list)
    points: list[DimToWarmPoint] = field(default_factory=list)

    def evaluate(self, brightness: int) -> int:
        """Evaluate color temperature (Kelvin) for given brightness (0-100%)."""
        if not self.points:
            return DEFAULT_COLOR_TEMP

        if len(self.points) == 1:
            return self.points[0].temp

        # Clamping
        if brightness <= self.points[0].brightness:
            return self.points[0].temp
        if brightness >= self.points[-1].brightness:
            return self.points[-1].temp

        # Piecewise linear interpolation
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            if p1.brightness <= brightness <= p2.brightness:
                if p2.brightness == p1.brightness:
                    return p1.temp
                fraction = (brightness - p1.brightness) / (p2.brightness - p1.brightness)
                return interpolate_scalar(p1.temp, p2.temp, fraction)

        return self.points[-1].temp


@dataclass(frozen=True)
class ScheduleStep:
    """A single scheduled checkpoint defining target light parameters at a given time."""

    time: time
    brightness: int
    temp: int | None = None
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


def parse_curve_points(raw_points: Any) -> list[DimToWarmPoint]:
    """Parse curve points from list of dicts or list of [brightness, temp] pairs."""
    if not raw_points or not isinstance(raw_points, (list, tuple)):
        return []

    points: list[DimToWarmPoint] = []
    for item in raw_points:
        b_val = None
        t_val = None
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            b_val = item[0]
            t_val = item[1]
        elif isinstance(item, dict):
            b_val = item.get("brightness", item.get("b", item.get("dim_to_warm", item.get("dimm_to_warm"))))
            t_val = item.get("temp", item.get("k", item.get("kelvin", item.get("color_temp"))))

        if b_val is not None and t_val is not None:
            try:
                b_int = int(str(b_val).rstrip("%").strip())
                t_int = int(str(t_val).rstrip("kK").strip())
                points.append(DimToWarmPoint(brightness=b_int, temp=t_int))
            except (ValueError, TypeError):
                continue

    points.sort(key=lambda pt: pt.brightness)
    return points


def parse_dim_to_warm_curves(
    data: Any,
) -> tuple[dict[str, DimToWarmCurve], dict[str, DimToWarmCurve]]:
    """Parse curve definitions into (curves_by_name, curves_by_light)."""
    curves_by_name: dict[str, DimToWarmCurve] = {}
    curves_by_light: dict[str, DimToWarmCurve] = {}

    if not data:
        return curves_by_name, curves_by_light

    raw_items: list[tuple[str, dict]] = []
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict):
                raw_items.append((str(key), val))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                name = str(item.get("name", f"curve_{len(raw_items)+1}"))
                raw_items.append((name, item))

    for name, item in raw_items:
        raw_lights = item.get("lights", [])
        if isinstance(raw_lights, str):
            lights = [raw_lights]
        elif isinstance(raw_lights, (list, tuple)):
            lights = [str(lt) for lt in raw_lights]
        else:
            lights = []

        raw_points = item.get("curve", item.get("points", []))
        points = parse_curve_points(raw_points)

        curve = DimToWarmCurve(name=name, lights=lights, points=points)
        curves_by_name[name] = curve
        for light_id in lights:
            curves_by_light[light_id] = curve

    return curves_by_name, curves_by_light


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
    b_val = data.get("brightness", data.get("dim_to_warm", data.get("dimm_to_warm", 100)))
    brightness = int(b_val)

    temp = None
    if "temp" in data and data["temp"] is not None:
        temp = int(data["temp"])

    light_overrides: dict[str, LightOverride] = {}
    if "lights" in data and isinstance(data["lights"], dict):
        for light_id, props in data["lights"].items():
            if isinstance(props, dict):
                b = None
                b_prop = props.get("brightness", props.get("dim_to_warm", props.get("dimm_to_warm")))
                if b_prop is not None:
                    b = int(b_prop)
                k = int(props["temp"]) if "temp" in props and props["temp"] is not None else None
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


def get_step_value(
    step: ScheduleStep,
    light_id: str,
    prop: str,
    light_curves: dict[str, DimToWarmCurve] | None = None,
) -> int | None:
    """Extract property value (brightness or temp) with per-light override."""
    if light_id in step.lights:
        override = step.lights[light_id]
        if prop == "brightness" and override.brightness is not None:
            return override.brightness
        if prop == "temp":
            if override.temp is not None:
                return override.temp
            if override.brightness is not None and light_curves and light_id in light_curves:
                return None

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
    light_curves: dict[str, DimToWarmCurve] | None = None,
) -> tuple[int, int]:
    """Calculate target (brightness_pct, color_temp_kelvin) for a light in transition."""
    if transition.total_seconds <= 0:
        fraction = 0.0
    else:
        fraction = transition.seconds_from_start / transition.total_seconds

    b_start = get_step_value(transition.start_step, light_id, "brightness", light_curves)
    b_end = get_step_value(transition.end_step, light_id, "brightness", light_curves)
    if b_start is None:
        b_start = 100
    if b_end is None:
        b_end = 100
    brightness = interpolate_scalar(b_start, b_end, fraction)

    curve = light_curves.get(light_id) if light_curves else None
    t_start_step = get_step_value(transition.start_step, light_id, "temp", light_curves)
    t_end_step = get_step_value(transition.end_step, light_id, "temp", light_curves)

    if t_start_step is None and t_end_step is None:
        if curve is not None:
            temp = curve.evaluate(brightness)
        else:
            temp = DEFAULT_COLOR_TEMP
    else:
        if t_start_step is None:
            t_start = curve.evaluate(b_start) if curve is not None else DEFAULT_COLOR_TEMP
        else:
            t_start = t_start_step

        if t_end_step is None:
            t_end = curve.evaluate(b_end) if curve is not None else DEFAULT_COLOR_TEMP
        else:
            t_end = t_end_step

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
