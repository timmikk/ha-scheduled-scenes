"""Tests for coordinator runtime, services, and entity interactions."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.scheduled_scenes import async_setup
from custom_components.scheduled_scenes.const import (
    CONF_BRIGHTNESS_CURVES,
    CONF_CURVES,
    CONF_DISABLE_WHEN_LIGHTS_OFF,
    CONF_ENABLE_WHEN_LIGHT_TURN_ON,
    CONF_LIGHTS,
    CONF_NAME,
    CONF_SCHEDULE,
    DEFAULT_COLOR_TEMP,
    DOMAIN,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_TURN_ON,
)
from custom_components.scheduled_scenes.coordinator import ScheduledSceneProgram


async def test_coordinator_turn_on_and_off(hass: HomeAssistant) -> None:
    """Test turn_on and turn_off programmatic controls."""
    config = {
        CONF_NAME: "study",
        CONF_LIGHTS: ["light.desk"],
        CONF_SCHEDULE: [
            {"time": "08:00", "brightness": 100, "temp": 4000},
            {"time": "20:00", "brightness": 50, "temp": 2500},
        ],
    }
    program = ScheduledSceneProgram(hass, config)
    await program.async_start()

    calls = []

    async def mock_service(call: ServiceCall):
        calls.append((call.domain, call.service, call.data))

    hass.services.async_register("light", "turn_on", mock_service)
    hass.services.async_register("light", "turn_off", mock_service)

    try:
        # Turn On
        await program.async_turn_on(transition_time=1.0)
        assert program.enabled is True
        assert any(c[1] == "turn_on" and c[2]["entity_id"] == "light.desk" for c in calls)

        # Turn Off
        calls.clear()
        await program.async_turn_off(transition_time=1.0)
        assert program.enabled is False
        assert any(c[1] == "turn_off" and c[2]["entity_id"] == ["light.desk"] for c in calls)
    finally:
        await program.async_stop()


async def test_coordinator_dim_to_warm_curves(hass: HomeAssistant) -> None:
    """Test coordinator dim-to-warm curve resolution during transitions and service calls."""
    config = {
        CONF_NAME: "kitchen",
        CONF_LIGHTS: ["light.spot_1", "light.spot_2", "light.regular"],
        CONF_CURVES: {
            "warm_glow_spots": {
                "lights": ["light.spot_1", "light.spot_2"],
                "curve": [
                    {"brightness": 1, "temp": 2000},
                    {"brightness": 50, "temp": 2700},
                    {"brightness": 100, "temp": 4000},
                ],
            }
        },
        CONF_SCHEDULE: [
            {"time": "00:00", "brightness": 50},  # temp omitted -> curve evaluates at 50% = 2700K
            {"time": "23:59", "brightness": 50},
        ],
    }
    program = ScheduledSceneProgram(hass, config)
    await program.async_start()

    calls = []

    async def mock_service(call: ServiceCall):
        calls.append((call.domain, call.service, dict(call.data)))

    hass.services.async_register("light", "turn_on", mock_service)
    hass.services.async_register("light", "turn_off", mock_service)

    try:
        # Turn On: spot_1 and spot_2 get curve temp 2700, regular gets DEFAULT_COLOR_TEMP 2700
        await program.async_turn_on(transition_time=1.0)
        assert len(calls) == 3

        spot1_call = next(c for c in calls if c[2]["entity_id"] == "light.spot_1")
        assert spot1_call[2]["brightness_pct"] == 50
        assert spot1_call[2]["color_temp_kelvin"] == 2700

        spot2_call = next(c for c in calls if c[2]["entity_id"] == "light.spot_2")
        assert spot2_call[2]["brightness_pct"] == 50
        assert spot2_call[2]["color_temp_kelvin"] == 2700

        regular_call = next(c for c in calls if c[2]["entity_id"] == "light.regular")
        assert regular_call[2]["brightness_pct"] == 50
        assert regular_call[2]["color_temp_kelvin"] == DEFAULT_COLOR_TEMP
    finally:
        await program.async_stop()


async def test_coordinator_adjust_brightness_and_resume(hass: HomeAssistant) -> None:
    """Test manual brightness adjustments, stepping, estimation, and resume."""
    config = {
        CONF_NAME: "living_room",
        CONF_LIGHTS: ["light.living_accent", "light.living_ceiling"],
        CONF_BRIGHTNESS_CURVES: {
            "accent_curve": {
                "lights": ["light.living_accent"],
                "points": [[0, 0], [50, 100], [100, 100]],
            },
            "ceiling_curve": {
                "lights": ["light.living_ceiling"],
                "points": [[0, 0], [30, 0], [50, 30], [100, 100]],
            },
        },
        CONF_CURVES: {
            "dtw": {
                "lights": ["light.living_accent", "light.living_ceiling"],
                "points": [[1, 2000], [50, 2700], [100, 4000]],
            }
        },
        CONF_SCHEDULE: [
            {"time": "00:00", "brightness": 40},
            {"time": "23:59", "brightness": 40},
        ],
    }
    program = ScheduledSceneProgram(hass, config)
    await program.async_start()

    calls = []

    async def mock_service(call: ServiceCall):
        calls.append((call.domain, call.service, dict(call.data)))

    hass.services.async_register("light", "turn_on", mock_service)
    hass.services.async_register("light", "turn_off", mock_service)

    try:
        # Step 1: Physical state estimation.
        # Suppose accent is on with physical brightness 255 (100%), and ceiling is on with 77 (30%)
        # Invert accent(100) -> 50% room brightness, ceiling(30) -> 50% room brightness.
        # Average is 50%.
        hass.states.async_set("light.living_accent", "on", {"brightness": 255})
        hass.states.async_set("light.living_ceiling", "on", {"brightness": 77})

        # User presses "Increase brightness" (+10%): target room brightness should be 50 + 10 = 60%
        calls.clear()
        await program.async_adjust_brightness(step=10, transition=0.5)
        assert program.manual_brightness == 60

        # At room brightness 60%:
        # accent is at 100% (dtw gives 4000K)
        # ceiling is at interpolate(30, 100, (60-50)/50) = 44% (dtw gives interpolate(2700, 4000, 44/50...) -> ~2616 or similar)
        accent_call = next(c for c in calls if c[2]["entity_id"] == "light.living_accent")
        assert accent_call[2]["brightness_pct"] == 100
        assert accent_call[2]["color_temp_kelvin"] == 4000

        ceiling_call = next(c for c in calls if c[2]["entity_id"] == "light.living_ceiling")
        assert ceiling_call[2]["brightness_pct"] == 44

        # Subsequent step +10% follows manual_brightness without jitter: 60 + 10 = 70%
        calls.clear()
        await program.async_adjust_brightness(step=10, transition=0.5)
        assert program.manual_brightness == 70

        # Direct brightness set: 50%
        calls.clear()
        await program.async_adjust_brightness(brightness=50, transition=0.5)
        assert program.manual_brightness == 50
        accent_50 = next(c for c in calls if c[2]["entity_id"] == "light.living_accent")
        ceiling_50 = next(c for c in calls if c[2]["entity_id"] == "light.living_ceiling")
        assert accent_50[2]["brightness_pct"] == 100
        assert ceiling_50[2]["brightness_pct"] == 30

        # Setting brightness to 0 turns off lights
        calls.clear()
        await program.async_adjust_brightness(brightness=0, transition=0.5)
        assert program.manual_brightness == 0
        assert any(c[1] == "turn_off" for c in calls)

        # Resume schedule clears manual_brightness
        calls.clear()
        await program.async_resume_schedule()
        assert program.manual_brightness is None

        # When all lights turn off, manual_brightness is reset
        program.manual_brightness = 80
        hass.states.async_set("light.living_accent", "off")
        hass.states.async_set("light.living_ceiling", "off")
        await hass.async_block_till_done()
        # Trigger state change handler
        event_data = {"new_state": hass.states.get("light.living_ceiling")}
        from homeassistant.core import Event
        await program._async_light_state_change(Event("state_changed", event_data))
        assert program.manual_brightness is None
    finally:
        await program.async_stop()


async def test_coordinator_light_state_triggers(hass: HomeAssistant) -> None:
    """Test light triggers for auto-enable and auto-disable."""
    config = {
        CONF_NAME: "hallway",
        CONF_LIGHTS: ["light.hallway_1", "light.hallway_2"],
        CONF_ENABLE_WHEN_LIGHT_TURN_ON: True,
        CONF_DISABLE_WHEN_LIGHTS_OFF: True,
        CONF_SCHEDULE: [
            {"time": "08:00", "brightness": 100, "temp": 4000},
            {"time": "20:00", "brightness": 50, "temp": 2500},
        ],
    }
    program = ScheduledSceneProgram(hass, config)
    await program.async_start()

    calls = []

    async def mock_service(call: ServiceCall):
        calls.append((call.domain, call.service, call.data))

    hass.services.async_register("light", "turn_on", mock_service)

    try:
        hass.states.async_set("light.hallway_1", "off")
        hass.states.async_set("light.hallway_2", "off")
        await hass.async_block_till_done()

        hass.states.async_set("light.hallway_1", "on")
        await hass.async_block_till_done()
        assert program.enabled is True

        hass.states.async_set("light.hallway_1", "off")
        await hass.async_block_till_done()
        assert program.enabled is False
    finally:
        await program.async_stop()


async def test_integration_setup_and_services(hass: HomeAssistant) -> None:
    """Test full integration config entry lifecycle and domain services."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Lounge",
        data={
            CONF_NAME: "lounge",
            CONF_LIGHTS: ["light.lounge"],
            CONF_SCHEDULE: [
                {"time": "07:00", "brightness": 50, "temp": 3000},
                {"time": "19:00", "brightness": 80, "temp": 4000},
            ],
        },
    )
    entry.add_to_hass(hass)

    light_calls = []

    async def mock_light_service(call: ServiceCall):
        light_calls.append((call.service, call.data))

    hass.services.async_register("light", "turn_on", mock_light_service)
    hass.services.async_register("light", "turn_off", mock_light_service)

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    switch_state = hass.states.get("switch.schedule_lounge")
    assert switch_state is not None
    assert switch_state.state == "on"

    sensor_state = hass.states.get("sensor.lounge_schedule_phase")
    assert sensor_state is not None

    await hass.services.async_call(DOMAIN, SERVICE_TURN_ON, {"entity_id": "switch.schedule_lounge"})
    await hass.async_block_till_done()
    assert any(c[0] == "turn_on" for c in light_calls)

    await hass.services.async_call(DOMAIN, SERVICE_DISABLE, {"entity_id": "switch.schedule_lounge"})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_lounge").state == "off"

    await hass.services.async_call(DOMAIN, SERVICE_ENABLE, {"entity_id": "switch.schedule_lounge"})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_lounge").state == "on"

    await hass.services.async_call(DOMAIN, "lounge_turn_on", {})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_lounge").state == "on"

    await hass.services.async_call(DOMAIN, "lounge_turn_off", {})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_lounge").state == "off"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_coordinator_duration_disable_timer(hass: HomeAssistant) -> None:
    """Test auto-re-enable after duration timer expires."""
    config = {
        CONF_NAME: "patio",
        CONF_LIGHTS: ["light.patio"],
        CONF_SCHEDULE: [
            {"time": "08:00", "brightness": 100, "temp": 4000},
            {"time": "20:00", "brightness": 50, "temp": 2500},
        ],
    }
    program = ScheduledSceneProgram(hass, config)
    await program.async_start()
    try:
        program.set_enabled(False, duration=1)
        assert program.enabled is False
        assert program._unsub_disable_timer is not None

        program.set_enabled(True)
        assert program.enabled is True
        assert program._unsub_disable_timer is None
    finally:
        await program.async_stop()


async def test_switch_and_sensor_entities(hass: HomeAssistant) -> None:
    """Test switch and sensor entity states and callbacks."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Office",
        data={
            CONF_NAME: "office",
            CONF_LIGHTS: ["light.office"],
            CONF_SCHEDULE: [
                {"time": "08:00", "brightness": 100, "temp": 4000},
                {"time": "20:00", "brightness": 50, "temp": 2500},
            ],
        },
    )
    entry.add_to_hass(hass)

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.schedule_office"})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_office").state == "off"

    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.schedule_office"})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_office").state == "on"

    sensor = hass.states.get("sensor.office_schedule_phase")
    assert sensor is not None
    assert "start_time" in sensor.attributes
    assert "end_time" in sensor.attributes
    assert "start_brightness" in sensor.attributes
    assert "end_brightness" in sensor.attributes

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
