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
                fraction = (brightness - p1.brightness) / (
                    p2.brightness - p1.brightness
                )
                return interpolate_scalar(p1.temp, p2.temp, fraction)

        return self.points[-1].temp


@dataclass(frozen=True)
class BrightnessPoint:
    """A single coordinate point on a room brightness curve."""

    room_brightness: int
    light_brightness: int


@dataclass(frozen=True)
class BrightnessCurve:
    """A room brightness curve mapping room brightness (0-100%) to light brightness (0-100%)."""

    name: str
    lights: list[str] = field(default_factory=list)
    points: list[BrightnessPoint] = field(default_factory=list)

    def evaluate(self, room_brightness: int) -> int:
        """Evaluate light brightness for given room brightness (0-100%)."""
        if not self.points:
            return max(0, min(100, room_brightness))

        if len(self.points) == 1:
            return max(0, min(100, self.points[0].light_brightness))

        # Clamping
        if room_brightness <= self.points[0].room_brightness:
            return max(0, min(100, self.points[0].light_brightness))
        if room_brightness >= self.points[-1].room_brightness:
            return max(0, min(100, self.points[-1].light_brightness))

        # Piecewise linear interpolation
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            if p1.room_brightness <= room_brightness <= p2.room_brightness:
                if p2.room_brightness == p1.room_brightness:
                    return max(0, min(100, p1.light_brightness))
                fraction = (room_brightness - p1.room_brightness) / (
                    p2.room_brightness - p1.room_brightness
                )
                val = interpolate_scalar(
                    p1.light_brightness, p2.light_brightness, fraction
                )
                return max(0, min(100, val))

        return max(0, min(100, self.points[-1].light_brightness))

    def invert(self, light_brightness: int) -> int:
        """Estimate room brightness (0-100%) corresponding to a light brightness."""
        if not self.points:
            return max(0, min(100, light_brightness))

        if len(self.points) == 1:
            return max(0, min(100, self.points[0].room_brightness))

        all_b = [p.light_brightness for p in self.points]
        min_b = min(all_b)
        max_b = max(all_b)

        if light_brightness < min_b:
            for p in self.points:
                if p.light_brightness == min_b:
                    return max(0, min(100, p.room_brightness))
            return max(0, min(100, self.points[0].room_brightness))

        if light_brightness > max_b:
            for p in reversed(self.points):
                if p.light_brightness == max_b:
                    return max(0, min(100, p.room_brightness))
            return max(0, min(100, self.points[-1].room_brightness))

        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            seg_min = min(p1.light_brightness, p2.light_brightness)
            seg_max = max(p1.light_brightness, p2.light_brightness)
            if seg_min <= light_brightness <= seg_max:
                if p2.light_brightness == p1.light_brightness:
                    return max(0, min(100, p1.room_brightness))
                fraction = (light_brightness - p1.light_brightness) / (
                    p2.light_brightness - p1.light_brightness
                )
                val = interpolate_scalar(
                    p1.room_brightness, p2.room_brightness, fraction
                )
                return max(0, min(100, val))

        return max(0, min(100, self.points[-1].room_brightness))


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
            b_val = item.get(
                "brightness",
                item.get("b", item.get("dim_to_warm", item.get("dimm_to_warm"))),
            )
            t_val = item.get(
                "temp", item.get("k", item.get("kelvin", item.get("color_temp")))
            )

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
                name = str(item.get("name", f"curve_{len(raw_items) + 1}"))
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


def parse_brightness_points(raw_points: Any) -> list[BrightnessPoint]:
    """Parse brightness curve points from list of dicts or list of [room_b, light_b] pairs."""
    if not raw_points or not isinstance(raw_points, (list, tuple)):
        return []

    points: list[BrightnessPoint] = []
    for item in raw_points:
        r_val = None
        l_val = None
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            r_val = item[0]
            l_val = item[1]
        elif isinstance(item, dict):
            r_val = item.get(
                "room_brightness", item.get("room", item.get("r", item.get("room_pct")))
            )
            l_val = item.get(
                "light_brightness",
                item.get("light", item.get("brightness", item.get("b"))),
            )

        if r_val is not None and l_val is not None:
            try:
                r_int = int(str(r_val).rstrip("%").strip())
                l_int = int(str(l_val).rstrip("%").strip())
                points.append(
                    BrightnessPoint(room_brightness=r_int, light_brightness=l_int)
                )
            except (ValueError, TypeError):
                continue

    points.sort(key=lambda pt: pt.room_brightness)
    return points


def parse_brightness_curves(
    data: Any,
) -> tuple[dict[str, BrightnessCurve], dict[str, BrightnessCurve]]:
    """Parse brightness curve definitions into (curves_by_name, curves_by_light)."""
    curves_by_name: dict[str, BrightnessCurve] = {}
    curves_by_light: dict[str, BrightnessCurve] = {}

    if not data:
        return curves_by_name, curves_by_light

    raw_items: list[tuple[str, dict]] = []
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict):
                raw_items.append((str(key), val))
            elif isinstance(val, (list, tuple)):
                raw_items.append((str(key), {"lights": [str(key)], "points": val}))
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                name = str(item.get("name", f"brightness_curve_{len(raw_items) + 1}"))
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
        points = parse_brightness_points(raw_points)

        curve = BrightnessCurve(name=name, lights=lights, points=points)
        curves_by_name[name] = curve
        for light_id in lights:
            curves_by_light[light_id] = curve

    return curves_by_name, curves_by_light


def estimate_room_brightness(
    current_light_brightnesses: dict[str, int],
    brightness_curves: dict[str, BrightnessCurve] | None = None,
) -> int:
    """Estimate overall room brightness (0-100%) from active light brightness states."""
    if not current_light_brightnesses:
        return 0

    estimates: list[int] = []
    for light_id, b in current_light_brightnesses.items():
        if b <= 0:
            continue
        if brightness_curves and light_id in brightness_curves:
            est = brightness_curves[light_id].invert(b)
        else:
            est = b
        estimates.append(est)

    if not estimates:
        return 0

    avg = round(sum(estimates) / len(estimates))
    return max(0, min(100, avg))


def calculate_manual_light_state(
    room_brightness: int,
    light_id: str,
    brightness_curves: dict[str, BrightnessCurve] | None = None,
    dim_to_warm_curves: dict[str, DimToWarmCurve] | None = None,
    default_temp: int = DEFAULT_COLOR_TEMP,
    manual_color_temp: int | None = None,
) -> tuple[int, int]:
    """Calculate target (brightness_pct, color_temp_kelvin) for a light under manual room brightness."""
    clamped_room_b = max(0, min(100, room_brightness))

    if brightness_curves and light_id in brightness_curves:
        light_b = brightness_curves[light_id].evaluate(clamped_room_b)
    else:
        light_b = clamped_room_b

    light_b = max(0, min(100, light_b))

    if manual_color_temp is not None:
        temp = manual_color_temp
    elif dim_to_warm_curves and light_id in dim_to_warm_curves:
        temp = dim_to_warm_curves[light_id].evaluate(light_b)
    else:
        temp = default_temp

    return light_b, temp


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
    b_val = data.get(
        "brightness", data.get("dim_to_warm", data.get("dimm_to_warm", 100))
    )
    brightness = int(b_val)

    temp = None
    if "temp" in data and data["temp"] is not None:
        temp = int(data["temp"])

    light_overrides: dict[str, LightOverride] = {}
    if "lights" in data and isinstance(data["lights"], dict):
        for light_id, props in data["lights"].items():
            if isinstance(props, dict):
                b = None
                b_prop = props.get(
                    "brightness", props.get("dim_to_warm", props.get("dimm_to_warm"))
                )
                if b_prop is not None:
                    b = int(b_prop)
                k = (
                    int(props["temp"])
                    if "temp" in props and props["temp"] is not None
                    else None
                )
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
            seconds_from_start=max(
                0.0, (now - start_dt.replace(tzinfo=None)).total_seconds()
            ),
        )

    today = now.date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    all_step_dts: list[tuple[datetime, ScheduleStep]] = []
    for d in (yesterday, today, tomorrow):
        for s in steps:
            all_step_dts.append((datetime.combine(d, s.time), s))

    for i in range(len(all_step_dts) - 1):
        start_dt, start_step = all_step_dts[i]
        end_dt, end_step = all_step_dts[i + 1]

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
    brightness_curves: dict[str, BrightnessCurve] | None = None,
    brightness_offset: int = 0,
) -> int | None:
    """Extract property value (brightness or temp) with per-light override."""
    if light_id in step.lights:
        override = step.lights[light_id]
        if prop == "brightness" and override.brightness is not None:
            return max(0, min(100, override.brightness + brightness_offset))
        if prop == "temp":
            if override.temp is not None:
                return override.temp
            if (
                override.brightness is not None
                and light_curves
                and light_id in light_curves
            ):
                return None

    if prop == "brightness":
        shifted_room_b = max(0, min(100, step.brightness + brightness_offset))
        if brightness_curves and light_id in brightness_curves:
            return brightness_curves[light_id].evaluate(shifted_room_b)
        return shifted_room_b
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
    brightness_curves: dict[str, BrightnessCurve] | None = None,
    brightness_offset: int = 0,
) -> tuple[int, int]:
    """Calculate target (brightness_pct, color_temp_kelvin) for a light in transition."""
    if transition.total_seconds <= 0:
        fraction = 0.0
    else:
        fraction = transition.seconds_from_start / transition.total_seconds

    b_start = get_step_value(
        transition.start_step,
        light_id,
        "brightness",
        light_curves,
        brightness_curves,
        brightness_offset,
    )
    b_end = get_step_value(
        transition.end_step,
        light_id,
        "brightness",
        light_curves,
        brightness_curves,
        brightness_offset,
    )
    if b_start is None:
        b_start = max(0, min(100, 100 + brightness_offset))
    if b_end is None:
        b_end = max(0, min(100, 100 + brightness_offset))
    brightness = interpolate_scalar(b_start, b_end, fraction)

    curve = light_curves.get(light_id) if light_curves else None
    t_start_step = get_step_value(
        transition.start_step,
        light_id,
        "temp",
        light_curves,
        brightness_curves,
        brightness_offset,
    )
    t_end_step = get_step_value(
        transition.end_step,
        light_id,
        "temp",
        light_curves,
        brightness_curves,
        brightness_offset,
    )

    if t_start_step is None and t_end_step is None:
        if curve is not None:
            temp = curve.evaluate(brightness)
        else:
            temp = DEFAULT_COLOR_TEMP
    else:
        if t_start_step is None:
            t_start = (
                curve.evaluate(b_start) if curve is not None else DEFAULT_COLOR_TEMP
            )
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
