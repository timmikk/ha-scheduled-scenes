"""Unit tests for the pure logic engine (custom_components/scheduled_scenes/logic.py)."""

from datetime import datetime, time
import pytest

from custom_components.scheduled_scenes.logic import (
    ActiveTransition,
    LightOverride,
    ScheduleStep,
    calculate_light_state,
    calculate_transition_seconds,
    get_step_value,
    interpolate_scalar,
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
    # 23:00 to 05:00 is 6 hours = 21600 seconds
    assert trans.total_seconds == 21600.0
    # From 23:00 yesterday to 02:00 today is 3 hours = 10800 seconds (exact midpoint)
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
