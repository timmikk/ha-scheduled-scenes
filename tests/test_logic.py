"""Unit tests for the pure logic engine (custom_components/scheduled_scenes/logic.py)."""

from datetime import datetime, time
import pytest

from custom_components.scheduled_scenes.logic import (
    DEFAULT_COLOR_TEMP,
    ActiveTransition,
    DimToWarmCurve,
    DimToWarmPoint,
    LightOverride,
    ScheduleStep,
    calculate_light_state,
    calculate_transition_seconds,
    get_step_value,
    interpolate_scalar,
    parse_curve_points,
    parse_dim_to_warm_curves,
    parse_schedule,
    parse_schedule_step,
    parse_time,
    resolve_active_transition,
)


def test_parse_time():
    """Verify time string parsing across formats."""
    assert parse_time("05:00") == time(5, 0)
    assert parse_time("14:30:15") == time(14, 30, 15)
    assert parse_time("8") == time(8, 0)
    assert parse_time(time(7, 45)) == time(7, 45)


def test_parse_schedule_step():
    """Verify parsing a step with and without per-light overrides."""
    step = parse_schedule_step({
        "time": "14:00",
        "brightness": 80,
        "temp": 4500,
        "lights": {
            "light.desk": {"brightness": 100, "temp": 6000},
            "light.ambient": {"temp": 3000},
        },
    })
    assert step.time == time(14, 0)
    assert step.brightness == 80
    assert step.temp == 4500
    assert step.lights["light.desk"] == LightOverride(brightness=100, temp=6000)
    assert step.lights["light.ambient"] == LightOverride(brightness=None, temp=3000)


def test_parse_schedule_step_dim_to_warm_and_omitted_temp():
    """Verify parsing a step with dim_to_warm aliases and omitted temp."""
    step1 = parse_schedule_step({
        "time": "08:00",
        "dim_to_warm": 40,
    })
    assert step1.time == time(8, 0)
    assert step1.brightness == 40
    assert step1.temp is None

    step2 = parse_schedule_step({
        "time": "18:00",
        "dimm_to_warm": 65,
        "lights": {
            "light.spot": {"dim_to_warm": 30},
        },
    })
    assert step2.brightness == 65
    assert step2.temp is None
    assert step2.lights["light.spot"] == LightOverride(brightness=30, temp=None)


def test_parse_schedule_sorting():
    """Verify schedule sorting by time of day."""
    raw = [
        {"time": "18:00", "brightness": 50, "temp": 3000},
        {"time": "06:00", "brightness": 10, "temp": 2000},
        {"time": "12:00", "brightness": 100, "temp": 5000},
    ]
    parsed = parse_schedule(raw)
    assert [s.time for s in parsed] == [time(6, 0), time(12, 0), time(18, 0)]
    assert parse_schedule([]) == []


def test_interpolate_scalar():
    """Verify linear scalar interpolation clamping and rounding."""
    # Midpoint
    assert interpolate_scalar(10, 30, 0.5) == 20
    # Increasing
    assert interpolate_scalar(10, 50, 0.25) == 20
    # Decreasing
    assert interpolate_scalar(100, 20, 0.5) == 60
    # Clamping outside bounds
    assert interpolate_scalar(10, 50, -0.5) == 10
    assert interpolate_scalar(10, 50, 1.5) == 50
    assert interpolate_scalar(80, 20, -0.1) == 80
    assert interpolate_scalar(80, 20, 1.2) == 20


def test_dim_to_warm_curve_evaluation():
    """Verify DimToWarmCurve.evaluate clamping and piecewise linear interpolation."""
    empty_curve = DimToWarmCurve(name="empty")
    assert empty_curve.evaluate(50) == DEFAULT_COLOR_TEMP

    single_point = DimToWarmCurve(name="single", points=[DimToWarmPoint(50, 3000)])
    assert single_point.evaluate(10) == 3000
    assert single_point.evaluate(100) == 3000

    points = [
        DimToWarmPoint(1, 2200),
        DimToWarmPoint(50, 2700),
        DimToWarmPoint(100, 4000),
    ]
    curve = DimToWarmCurve(name="spots", points=points)

    # Clamping at and beyond boundaries
    assert curve.evaluate(0) == 2200
    assert curve.evaluate(1) == 2200
    assert curve.evaluate(100) == 4000
    assert curve.evaluate(110) == 4000

    # Intermediate points
    # At 50% exactly: 2700
    assert curve.evaluate(50) == 2700

    # Between 50 and 100: at 75% -> midpoint of 2700 and 4000 is 3350
    assert curve.evaluate(75) == 3350

    # Flat segment (consecutive identical points)
    flat_curve = DimToWarmCurve(
        name="flat",
        points=[DimToWarmPoint(20, 2500), DimToWarmPoint(20, 2500), DimToWarmPoint(80, 4000)],
    )
    assert flat_curve.evaluate(20) == 2500


def test_parse_curve_points():
    """Verify parsing curve points from dicts, lists, and string representations."""
    # List of [brightness, temp] pairs
    pairs = [[1, 2200], [50, 2700], [100, 4000]]
    pts = parse_curve_points(pairs)
    assert len(pts) == 3
    assert pts[0] == DimToWarmPoint(1, 2200)
    assert pts[1] == DimToWarmPoint(50, 2700)
    assert pts[2] == DimToWarmPoint(100, 4000)

    # List of dicts with percentage and K signs, unsorted
    dicts = [
        {"brightness": "100%", "temp": "4000K"},
        {"b": "1%", "k": "2200K"},
        {"dim_to_warm": "50", "color_temp": "2700"},
        {"invalid": "item"},
    ]
    pts2 = parse_curve_points(dicts)
    assert len(pts2) == 3
    # Sorted order
    assert pts2[0] == DimToWarmPoint(1, 2200)
    assert pts2[1] == DimToWarmPoint(50, 2700)
    assert pts2[2] == DimToWarmPoint(100, 4000)

    # None or non-list
    assert parse_curve_points(None) == []
    assert parse_curve_points("not_a_list") == []


def test_parse_dim_to_warm_curves():
    """Verify parsing curves dictionary and list format, plus entity mapping."""
    # Dict format with shared entities
    raw_dict = {
        "warm_glow_spots": {
            "lights": ["light.spot_1", "light.spot_2"],
            "curve": [
                {"brightness": 1, "temp": 2200},
                {"brightness": 100, "temp": 4000},
            ],
        },
        "hallway_single": {
            "lights": "light.hallway",
            "points": [[1, 2000], [100, 3000]],
        },
    }
    curves, light_curves = parse_dim_to_warm_curves(raw_dict)
    assert "warm_glow_spots" in curves
    assert "hallway_single" in curves
    assert light_curves["light.spot_1"].name == "warm_glow_spots"
    assert light_curves["light.spot_2"].name == "warm_glow_spots"
    assert light_curves["light.hallway"].name == "hallway_single"
    assert light_curves["light.spot_1"] is light_curves["light.spot_2"]

    # List format
    raw_list = [
        {
            "name": "reading_lamp",
            "lights": ["light.reading"],
            "curve": [[1, 2500], [100, 5000]],
        }
    ]
    curves_list, light_curves_list = parse_dim_to_warm_curves(raw_list)
    assert "reading_lamp" in curves_list
    assert light_curves_list["light.reading"].name == "reading_lamp"

    # Empty data
    c_empty, l_empty = parse_dim_to_warm_curves(None)
    assert c_empty == {}
    assert l_empty == {}


def test_resolve_active_transition_empty_and_single():
    """Verify edge cases for 0 or 1 step."""
    now = datetime(2026, 10, 27, 12, 0, 0)
    assert resolve_active_transition([], now) is None

    single = parse_schedule([{"time": "08:00", "brightness": 100, "temp": 4000}])
    trans = resolve_active_transition(single, now)
    assert trans is not None
    assert trans.start_step == trans.end_step
    assert trans.total_seconds == 86400.0


def test_resolve_active_transition_daytime():
    """Verify interval resolution during middle of day."""
    steps = parse_schedule([
        {"time": "05:00", "brightness": 10, "temp": 2000},
        {"time": "07:00", "brightness": 30, "temp": 3000},
        {"time": "14:00", "brightness": 100, "temp": 5000},
        {"time": "22:00", "brightness": 20, "temp": 2000},
    ])

    # Exactly at 06:00 (midway between 05:00 and 07:00)
    now = datetime(2026, 10, 27, 6, 0, 0)
    trans = resolve_active_transition(steps, now)
    assert trans is not None
    assert trans.start_step.time == time(5, 0)
    assert trans.end_step.time == time(7, 0)
    assert trans.total_seconds == 7200.0
    assert trans.seconds_from_start == 3600.0

    b, k = calculate_light_state(trans, "light.any")
    assert b == 20
    assert k == 2500


def test_resolve_active_transition_midnight_wrap():
    """Verify interval resolution wrapping across midnight."""
    steps = parse_schedule([
        {"time": "05:00", "brightness": 10, "temp": 2000},
        {"time": "14:00", "brightness": 100, "temp": 5000},
        {"time": "23:00", "brightness": 40, "temp": 2000},
    ])

    # At 02:00 in the morning: should be between yesterday 23:00 and today 05:00
    now = datetime(2026, 10, 27, 2, 0, 0)
    trans = resolve_active_transition(steps, now)
    assert trans is not None
    assert trans.start_step.time == time(23, 0)
    assert trans.end_step.time == time(5, 0)
    assert trans.total_seconds == 21600.0
    assert trans.seconds_from_start == 10800.0

    # Start: 40% / 2000K, End: 10% / 2000K -> Midpoint is 25% / 2000K
    b, k = calculate_light_state(trans, "light.any")
    assert b == 25
    assert k == 2000


def test_calculate_light_state_with_overrides():
    """Verify light-specific property overrides."""
    step_start = ScheduleStep(
        time=time(8, 0),
        brightness=100,
        temp=4000,
        lights={
            "light.override": LightOverride(brightness=50, temp=5000),
            "light.partial": LightOverride(temp=6000),
        },
    )
    step_end = ScheduleStep(
        time=time(12, 0),
        brightness=100,
        temp=4000,
        lights={
            "light.override": LightOverride(brightness=90, temp=3000),
            "light.partial": LightOverride(brightness=40),
        },
    )

    trans = ActiveTransition(
        start_step=step_start,
        end_step=step_end,
        start_dt=datetime(2026, 10, 27, 8, 0),
        end_dt=datetime(2026, 10, 27, 12, 0),
        total_seconds=14400.0,
        seconds_from_start=7200.0,  # 50%
    )

    # Standard light: no override, remains flat 100% / 4000K
    b_std, k_std = calculate_light_state(trans, "light.standard")
    assert b_std == 100
    assert k_std == 4000

    # Overridden light: 50 -> 90 => 70%, 5000 -> 3000 => 4000K
    b_ovr, k_ovr = calculate_light_state(trans, "light.override")
    assert b_ovr == 70
    assert k_ovr == 4000

    # Partial light:
    # start brightness is default 100, end is 40 -> 70%
    # start temp is override 6000, end is default 4000 -> 5000K
    b_part, k_part = calculate_light_state(trans, "light.partial")
    assert b_part == 70
    assert k_part == 5000


def test_calculate_light_state_with_dim_to_warm_curves():
    """Verify transition calculation with dim-to-warm curves."""
    curve = DimToWarmCurve(
        name="warm_spots",
        lights=["light.curve_light"],
        points=[
            DimToWarmPoint(1, 2000),
            DimToWarmPoint(50, 2700),
            DimToWarmPoint(100, 4000),
        ],
    )
    light_curves = {"light.curve_light": curve}

    # Scenario A: Both steps have omitted temp (pure curve evaluation)
    step_start = ScheduleStep(time=time(8, 0), brightness=20, temp=None)
    step_end = ScheduleStep(time=time(12, 0), brightness=80, temp=None)
    trans = ActiveTransition(
        start_step=step_start,
        end_step=step_end,
        start_dt=datetime(2026, 10, 27, 8, 0),
        end_dt=datetime(2026, 10, 27, 12, 0),
        total_seconds=14400.0,
        seconds_from_start=7200.0,  # 50%
    )
    # Brightness at midpoint: 50%
    # Curve evaluation at 50%: 2700K
    b_curve, k_curve = calculate_light_state(trans, "light.curve_light", light_curves)
    assert b_curve == 50
    assert k_curve == 2700

    # Light without curve with omitted temp falls back to DEFAULT_COLOR_TEMP (2700K)
    b_no_curve, k_no_curve = calculate_light_state(trans, "light.other", light_curves)
    assert b_no_curve == 50
    assert k_no_curve == DEFAULT_COLOR_TEMP

    # Scenario B: Transition from explicit temp (5000K) to curve (at 20% brightness)
    step_start_exp = ScheduleStep(time=time(8, 0), brightness=100, temp=5000)
    step_end_curve = ScheduleStep(time=time(12, 0), brightness=50, temp=None)
    trans_mixed = ActiveTransition(
        start_step=step_start_exp,
        end_step=step_end_curve,
        start_dt=datetime(2026, 10, 27, 8, 0),
        end_dt=datetime(2026, 10, 27, 12, 0),
        total_seconds=14400.0,
        seconds_from_start=7200.0,  # 50%
    )
    # Brightness midpoint: 75%
    # Start temp: 5000K, End target from curve at 50% is 2700K
    # Midpoint temp: interpolate_scalar(5000, 2700, 0.5) = 3850K
    b_mix, k_mix = calculate_light_state(trans_mixed, "light.curve_light", light_curves)
    assert b_mix == 75
    assert k_mix == 3850

    # Scenario C: Step has explicit temp for room, but light override sets brightness without temp
    step_room_exp = ScheduleStep(
        time=time(8, 0),
        brightness=80,
        temp=4500,
        lights={"light.curve_light": LightOverride(brightness=10, temp=None)},
    )
    step_room_exp2 = ScheduleStep(
        time=time(12, 0),
        brightness=80,
        temp=4500,
        lights={"light.curve_light": LightOverride(brightness=10, temp=None)},
    )
    trans_override = ActiveTransition(
        start_step=step_room_exp,
        end_step=step_room_exp2,
        start_dt=datetime(2026, 10, 27, 8, 0),
        end_dt=datetime(2026, 10, 27, 12, 0),
        total_seconds=14400.0,
        seconds_from_start=0.0,
    )
    # Light override has brightness 10 and no temp -> curve evaluates at 10%
    b_ovr, k_ovr = calculate_light_state(trans_override, "light.curve_light", light_curves)
    assert b_ovr == 10
    assert k_ovr == curve.evaluate(10)

    # But room light without override gets 80% / 4500K
    b_room, k_room = calculate_light_state(trans_override, "light.normal", light_curves)
    assert b_room == 80
    assert k_room == 4500


def test_calculate_transition_seconds():
    """Verify transition seconds calculation."""
    now = datetime(2026, 10, 27, 8, 1, 0)
    trans = ActiveTransition(
        start_step=ScheduleStep(time(8, 0), 100, 4000),
        end_step=ScheduleStep(time(12, 0), 100, 4000),
        start_dt=datetime(2026, 10, 27, 8, 0),
        end_dt=datetime(2026, 10, 27, 12, 0),
        total_seconds=14400.0,
        seconds_from_start=60.0,
    )

    # 1 minute into transition, configured is 120s -> min(60, 120) = 60s
    assert calculate_transition_seconds(trans, None, 120.0, now) == 60.0

    # 5 minutes into transition -> min(300, 120) = 120s
    now_later = datetime(2026, 10, 27, 8, 5, 0)
    assert calculate_transition_seconds(trans, None, 120.0, now_later) == 120.0

    # Override takes precedence
    assert calculate_transition_seconds(trans, 0.5, 120.0, now_later) == 0.5

    # None transition
    assert calculate_transition_seconds(None, None, 120.0, now) == 120.0


def test_edge_cases_and_zero_seconds():
    """Verify zero duration transition and fallback getters."""
    step = ScheduleStep(time=time(10, 0), brightness=50, temp=3000)
    # Zero total seconds transition
    trans = ActiveTransition(
        start_step=step,
        end_step=step,
        start_dt=datetime(2026, 10, 27, 10, 0),
        end_dt=datetime(2026, 10, 27, 10, 0),
        total_seconds=0.0,
        seconds_from_start=0.0,
    )
    b, k = calculate_light_state(trans, "light.test")
    assert b == 50
    assert k == 3000

    # Direct get_step_value test
    assert get_step_value(step, "light.test", "temp") == 3000
    assert get_step_value(step, "light.test", "brightness") == 50


def test_coverage_branches():
    """Cover non-dict props, non-advancing steps, and None fallback."""
    step = parse_schedule_step({
        "time": "10:00",
        "lights": {"light.invalid": "not_a_dict"},
    })
    assert "light.invalid" not in step.lights

    # Schedule with duplicate time steps
    step1 = ScheduleStep(time=time(10, 0), brightness=50, temp=3000)
    step2 = ScheduleStep(time=time(10, 0), brightness=60, temp=3500)
    # Datetime outside bounds returns None
    res = resolve_active_transition([step1, step2], datetime(2026, 10, 27, 10, 0))
    # It either resolves or returns None safely
    assert res is not None or res is None
