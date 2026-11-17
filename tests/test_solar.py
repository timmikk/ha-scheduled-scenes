from datetime import date

from custom_components.scheduled_scenes.solar import (
    elevation_crossing,
    resolve_sun_point,
    solar_noon,
)


def test_solar_noon_is_near_midday_at_greenwich() -> None:
    assert 710 < solar_noon(date(2024, 3, 20), 0) < 730


def test_elevation_crossings_bracket_noon() -> None:
    day = date(2024, 6, 21)
    rising = elevation_crossing(day, 51.5, 0, -0.833, "rising")
    setting = elevation_crossing(day, 51.5, 0, -0.833, "setting")
    assert (
        rising is not None
        and setting is not None
        and rising < solar_noon(day, 0) < setting
    )


def test_polar_night_has_no_sunrise() -> None:
    assert (
        resolve_sun_point(
            {"type": "sun", "event": "sunrise"}, date(2024, 12, 21), 89, 0
        )
        is None
    )


def test_civil_dawn_precedes_sunrise_and_time_offset_is_applied() -> None:
    day = date(2024, 6, 21)
    dawn = resolve_sun_point({"type": "sun", "event": "dawn"}, day, 51.5, 0)
    sunrise = resolve_sun_point({"type": "sun", "event": "sunrise"}, day, 51.5, 0)
    shifted = resolve_sun_point(
        {"type": "sun", "event": "sunrise", "offset_value": 30, "offset_unit": "time"},
        day,
        51.5,
        0,
    )
    assert dawn is not None and sunrise is not None and shifted is not None
    assert dawn < sunrise
    assert shifted == (sunrise + 30) % 1440


def test_polar_day_has_no_sunset() -> None:
    assert (
        resolve_sun_point({"type": "sun", "event": "sunset"}, date(2024, 6, 21), 89, 0)
        is None
    )
