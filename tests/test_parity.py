"""Parity tests validating the 5 production room schedules from pyscript/config.yaml."""

from datetime import datetime

from custom_components.scheduled_scenes.logic import (
    calculate_light_state,
    parse_schedule,
    resolve_active_transition,
)

# Golden configurations copied directly from home-assistant-config/pyscript/config.yaml
PRODUCTION_ROOMS = {
    "tyohuone": {
        "lights": ["light.valo_th_poyta"],
        "schedule": [
            {"time": "05:00", "brightness": 100, "temp": 2000},
            {"time": "07:00", "brightness": 100, "temp": 3000},
            {"time": "08:00", "brightness": 100, "temp": 4000},
            {"time": "14:00", "brightness": 100, "temp": 5000},
            {"time": "18:00", "brightness": 100, "temp": 4000},
            {"time": "23:00", "brightness": 100, "temp": 2000},
        ],
    },
    "olohuone": {
        "lights": [
            "light.oh_katto_1",
            "light.oh_katto_2",
            "light.olohuone_valonauha",
            "light.olohuone_vitriini",
        ],
        "schedule": [
            {"time": "05:00", "brightness": 50, "temp": 2000},
            {"time": "07:00", "brightness": 60, "temp": 2800},
            {"time": "08:00", "brightness": 100, "temp": 4000},
            {
                "time": "14:00",
                "brightness": 100,
                "temp": 5000,
                "lights": {
                    "light.olohuone_valonauha": {"temp": 6000},
                    "light.olohuone_vitriini": {"temp": 5000},
                },
            },
            {
                "time": "17:00",
                "brightness": 100,
                "temp": 4000,
                "lights": {"light.olohuone_valonauha": {"temp": 3000}},
            },
            {
                "time": "19:00",
                "brightness": 100,
                "temp": 3000,
                "lights": {
                    "light.olohuone_valonauha": {"temp": 2700, "brightness": 60}
                },
            },
            {
                "time": "20:00",
                "brightness": 70,
                "temp": 2500,
                "lights": {
                    "light.olohuone_valonauha": {"temp": 2300, "brightness": 50}
                },
            },
            {
                "time": "22:00",
                "brightness": 40,
                "temp": 2000,
                "lights": {"light.olohuone_valonauha": {"temp": 1000, "brightness": 1}},
            },
        ],
    },
    "ruokailutila": {
        "lights": [
            "light.keittio_1",
            "light.keittio_2",
            "light.keittio_valonauha_2",
            "light.ruokapoyta_1",
        ],
        "schedule": [
            {"time": "05:00", "brightness": 50, "temp": 2000},
            {"time": "07:00", "brightness": 70, "temp": 3000},
            {"time": "08:00", "brightness": 100, "temp": 4000},
            {"time": "14:00", "brightness": 100, "temp": 5000},
            {"time": "16:00", "brightness": 100, "temp": 5000},
            {"time": "19:00", "brightness": 70, "temp": 3000},
            {
                "time": "21:00",
                "brightness": 50,
                "temp": 2000,
                "lights": {
                    "light.keittio_valonauha_2": {"temp": 1000, "brightness": 30}
                },
            },
            {
                "time": "23:00",
                "brightness": 30,
                "temp": 2000,
                "lights": {
                    "light.keittio_valonauha_2": {"temp": 1000, "brightness": 1}
                },
            },
        ],
    },
}


def test_production_schedules_parse():
    """Verify that all production room schedules parse without errors."""
    for room, conf in PRODUCTION_ROOMS.items():
        steps = parse_schedule(conf["schedule"])
        assert len(steps) == len(conf["schedule"])


def test_tyohuone_24h_replay():
    """Verify 24-hour simulation of tyohuone room schedule."""
    steps = parse_schedule(PRODUCTION_ROOMS["tyohuone"]["schedule"])

    # 06:00 - halfway between 05:00 (temp: 2000) and 07:00 (temp: 3000)
    t1 = resolve_active_transition(steps, datetime(2026, 10, 27, 6, 0))
    assert t1 is not None
    b1, k1 = calculate_light_state(t1, "light.valo_th_poyta")
    assert b1 == 100
    assert k1 == 2500

    # 11:00 - halfway between 08:00 (temp: 4000) and 14:00 (temp: 5000)
    t2 = resolve_active_transition(steps, datetime(2026, 10, 27, 11, 0))
    assert t2 is not None
    b2, k2 = calculate_light_state(t2, "light.valo_th_poyta")
    assert b2 == 100
    assert k2 == 4500

    # 02:00 - between 23:00 (temp: 2000) and 05:00 (temp: 2000)
    t3 = resolve_active_transition(steps, datetime(2026, 10, 27, 2, 0))
    assert t3 is not None
    b3, k3 = calculate_light_state(t3, "light.valo_th_poyta")
    assert b3 == 100
    assert k3 == 2000


def test_olohuone_light_specific_overrides():
    """Verify that olohuone custom overrides for valonauha calculate correctly."""
    steps = parse_schedule(PRODUCTION_ROOMS["olohuone"]["schedule"])

    # At 14:00:
    # oh_katto_1 should have base temp 5000
    # olohuone_valonauha should have override temp 6000
    t1 = resolve_active_transition(steps, datetime(2026, 10, 27, 14, 0))
    assert t1 is not None

    b_katto, k_katto = calculate_light_state(t1, "light.oh_katto_1")
    assert b_katto == 100
    assert k_katto == 5000

    b_nauha, k_nauha = calculate_light_state(t1, "light.olohuone_valonauha")
    assert b_nauha == 100
    assert k_nauha == 6000

    # At 21:00 (midway between 20:00 and 22:00):
    # Base brightness: 70 -> 40 => 55
    # Base temp: 2500 -> 2000 => 2250
    # Valonauha brightness: 50 -> 1 => 26
    # Valonauha temp: 2300 -> 1000 => 1650
    t2 = resolve_active_transition(steps, datetime(2026, 10, 27, 21, 0))
    assert t2 is not None

    b_katto2, k_katto2 = calculate_light_state(t2, "light.oh_katto_1")
    assert b_katto2 == 55
    assert k_katto2 == 2250

    b_nauha2, k_nauha2 = calculate_light_state(t2, "light.olohuone_valonauha")
    assert b_nauha2 == 26
    assert k_nauha2 == 1650
