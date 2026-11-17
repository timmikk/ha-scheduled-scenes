"""Dependency-free NOAA-style solar event calculations shared with the Studio."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any


def solar_position(day: date, latitude: float, longitude: float) -> tuple[float, float]:
    """Return solar declination (degrees) and equation of time (minutes)."""
    n = day.timetuple().tm_yday
    gamma = 2 * math.pi / 365 * (n - 1)
    equation = 229.18 * (
        0.000075
        + 0.001868 * math.cos(gamma)
        - 0.032077 * math.sin(gamma)
        - 0.014615 * math.cos(2 * gamma)
        - 0.040849 * math.sin(2 * gamma)
    )
    declination = (
        (
            0.006918
            - 0.399912 * math.cos(gamma)
            + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma)
            + 0.000907 * math.sin(2 * gamma)
            - 0.002697 * math.cos(3 * gamma)
            + 0.00148 * math.sin(3 * gamma)
        )
        * 180
        / math.pi
    )
    return declination, equation


def solar_noon(day: date, longitude: float) -> float:
    return 720 - 4 * longitude - solar_position(day, 0, longitude)[1]


def elevation_crossing(
    day: date,
    latitude: float,
    longitude: float,
    elevation: float,
    direction: str = "rising",
) -> float | None:
    declination, _ = solar_position(day, latitude, longitude)
    lat, dec, alt = map(math.radians, (latitude, declination, elevation))
    cosine = (math.sin(alt) - math.sin(lat) * math.sin(dec)) / (
        math.cos(lat) * math.cos(dec)
    )
    if cosine < -1 or cosine > 1:
        return None
    hour_angle = math.degrees(math.acos(cosine))
    noon = solar_noon(day, longitude)
    return noon + (1 if direction == "setting" else -1) * 4 * hour_angle


def resolve_sun_point(
    config: Mapping[str, Any],
    day: datetime | date,
    latitude: float,
    longitude: float,
) -> int | None:
    """Resolve a sun definition to local solar-clock minutes (timezone handled by caller)."""
    date_value = day.date() if isinstance(day, datetime) else day
    event = config.get("event", "sunrise")
    direction = config.get("direction", "rising")
    if event == "solar_noon":
        minute: float | None = solar_noon(date_value, longitude)
    elif event in ("sunrise", "sunset", "dawn", "dusk"):
        alt = -6 if event in ("dawn", "dusk") else -0.833
        minute = elevation_crossing(
            date_value,
            latitude,
            longitude,
            alt,
            "rising" if event in ("sunrise", "dawn") else "setting",
        )
    elif event == "solar_midnight":
        minute = (solar_noon(date_value, longitude) + 720) % 1440
    elif event == "elevation":
        minute = elevation_crossing(
            date_value,
            latitude,
            longitude,
            float(config.get("elevation", 0)),
            direction,
        )
    else:
        return None
    if minute is None:
        return None
    offset = float(config.get("offset_value", 0) or 0)
    if config.get("offset_unit", "time") == "time":
        minute += offset
    elif event in ("elevation", "sunrise", "sunset", "dawn", "dusk"):
        base_altitude = (
            float(config.get("elevation", 0))
            if event == "elevation"
            else (-6 if event in ("dawn", "dusk") else -0.833)
        )
        target = base_altitude + offset
        target_direction = config.get(
            "direction", "setting" if event in ("sunset", "dusk") else "rising"
        )
        minute = elevation_crossing(
            date_value, latitude, longitude, target, target_direction
        )
        if minute is None:
            return None
    return round(minute) % 1440
