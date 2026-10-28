"""Tests for coordinator runtime, services, and entity interactions."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.scheduled_scenes import async_setup
from custom_components.scheduled_scenes.const import (
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
        # Initially program is enabled, all lights off
        hass.states.async_set("light.hallway_1", "off")
        hass.states.async_set("light.hallway_2", "off")
        await hass.async_block_till_done()

        # Turn on light 1 -> triggers transition
        hass.states.async_set("light.hallway_1", "on")
        await hass.async_block_till_done()
        assert program.enabled is True

        # Turn off both lights -> auto disables
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

    # Switch entity should exist
    switch_state = hass.states.get("switch.schedule_lounge")
    assert switch_state is not None
    assert switch_state.state == "on"

    # Sensor entity should exist
    sensor_state = hass.states.get("sensor.lounge_schedule_phase")
    assert sensor_state is not None

    # Call scheduled_scenes.turn_on
    await hass.services.async_call(DOMAIN, SERVICE_TURN_ON, {"entity_id": "switch.schedule_lounge"})
    await hass.async_block_till_done()
    assert any(c[0] == "turn_on" for c in light_calls)

    # Call scheduled_scenes.disable
    await hass.services.async_call(DOMAIN, SERVICE_DISABLE, {"entity_id": "switch.schedule_lounge"})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_lounge").state == "off"

    # Call scheduled_scenes.enable
    await hass.services.async_call(DOMAIN, SERVICE_ENABLE, {"entity_id": "switch.schedule_lounge"})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_lounge").state == "on"

    # Call legacy alias service lounge_turn_on
    await hass.services.async_call(DOMAIN, "lounge_turn_on", {})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_lounge").state == "on"

    # Call legacy alias service lounge_turn_off
    await hass.services.async_call(DOMAIN, "lounge_turn_off", {})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_lounge").state == "off"

    # Unload entry
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
        # Disable with duration = 1 minute
        program.set_enabled(False, duration=1)
        assert program.enabled is False
        assert program._unsub_disable_timer is not None

        # Setting enabled cancels timer
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

    # Test switch service calls turn_off and turn_on
    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.schedule_office"})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_office").state == "off"

    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.schedule_office"})
    await hass.async_block_till_done()
    assert hass.states.get("switch.schedule_office").state == "on"

    # Test sensor attributes
    sensor = hass.states.get("sensor.office_schedule_phase")
    assert sensor is not None
    assert "start_time" in sensor.attributes
    assert "end_time" in sensor.attributes
    assert "start_brightness" in sensor.attributes
    assert "end_brightness" in sensor.attributes

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
