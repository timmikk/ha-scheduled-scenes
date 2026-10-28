"""Tests for coordinator runtime, services, and entity interactions."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.scheduled_scenes import async_setup
from custom_components.scheduled_scenes.const import (
    ATTR_BRIGHTNESS,
    ATTR_STEP,
    CONF_BRIGHTNESS_CURVES,
    CONF_CURVES,
    CONF_DISABLE_WHEN_LIGHTS_OFF,
    CONF_ENABLE_WHEN_LIGHT_TURN_ON,
    CONF_LIGHTS,
    CONF_NAME,
    CONF_SCHEDULE,
    DEFAULT_COLOR_TEMP,
    DOMAIN,
    SERVICE_ADJUST_BRIGHTNESS,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_RESUME_SCHEDULE,
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


async def test_diagnostic_status_entities_lifecycle(hass: HomeAssistant) -> None:
    """Test complete lifecycle and transitions of diagnostic status entities."""
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

    light_calls = []

    async def mock_light_service(call: ServiceCall):
        light_calls.append((call.service, dict(call.data)))

    hass.services.async_register("light", "turn_on", mock_light_service)
    hass.services.async_register("light", "turn_off", mock_light_service)

    # Initial light state is off
    hass.states.async_set("light.office", "off")

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # 1. Initial State: lights off -> auto-off
    mode_state = hass.states.get("sensor.office_mode")
    assert mode_state is not None
    assert mode_state.state == "auto-off"

    brightness_state = hass.states.get("sensor.office_current_brightness")
    assert brightness_state is not None
    assert int(brightness_state.state) == 0

    command_state = hass.states.get("sensor.office_last_command")
    assert command_state is not None
    assert command_state.state == "none"

    dtw_state = hass.states.get("binary_sensor.office_dim_to_warm_in_use")
    assert dtw_state is not None
    assert dtw_state.state == "off"

    b_curve_state = hass.states.get("binary_sensor.office_brightness_curve_in_use")
    assert b_curve_state is not None
    assert b_curve_state.state == "off"

    prob_state = hass.states.get("binary_sensor.office_problem")
    assert prob_state is not None
    assert prob_state.state == "off"

    # 2. Lights turn on -> mode changes to auto, current brightness reflects physical brightness
    hass.states.async_set("light.office", "on", {"brightness": 128})
    await hass.async_block_till_done()

    mode_state = hass.states.get("sensor.office_mode")
    assert mode_state.state == "auto"

    brightness_state = hass.states.get("sensor.office_current_brightness")
    assert int(brightness_state.state) == 50

    # 3. Adjust brightness via step -> mode changes to manual, last command is step brightness
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ADJUST_BRIGHTNESS,
        {"entity_id": "switch.schedule_office", ATTR_STEP: 10},
    )
    await hass.async_block_till_done()

    mode_state = hass.states.get("sensor.office_mode")
    assert mode_state.state == "manual"
    assert mode_state.attributes["manual_override"] is True
    assert mode_state.attributes["manual_brightness"] == 60

    command_state = hass.states.get("sensor.office_last_command")
    assert command_state.state == "step brightness"
    assert command_state.attributes["details"]["step"] == 10

    brightness_state = hass.states.get("sensor.office_current_brightness")
    assert int(brightness_state.state) == 60

    # 4. Explicitly set brightness -> last command is set brightness
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ADJUST_BRIGHTNESS,
        {"entity_id": "switch.schedule_office", ATTR_BRIGHTNESS: 80},
    )
    await hass.async_block_till_done()

    command_state = hass.states.get("sensor.office_last_command")
    assert command_state.state == "set brightness"
    assert command_state.attributes["details"]["target_brightness"] == 80
    assert hass.states.get("sensor.office_current_brightness").state == "80"

    # 5. Resume schedule -> mode changes back to auto, last command is resume schedule
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESUME_SCHEDULE,
        {"entity_id": "switch.schedule_office"},
    )
    await hass.async_block_till_done()

    mode_state = hass.states.get("sensor.office_mode")
    assert mode_state.state == "auto"
    assert mode_state.attributes["manual_override"] is False

    command_state = hass.states.get("sensor.office_last_command")
    assert command_state.state == "resume schedule"

    # 6. Turn off lights -> mode becomes auto-off, last command is auto off
    hass.states.async_set("light.office", "off")
    await hass.async_block_till_done()

    mode_state = hass.states.get("sensor.office_mode")
    assert mode_state.state == "auto-off"

    command_state = hass.states.get("sensor.office_last_command")
    assert command_state.state == "auto off"

    # 7. Explicitly disable schedule via switch -> mode becomes off, command is disable
    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.schedule_office"})
    await hass.async_block_till_done()

    mode_state = hass.states.get("sensor.office_mode")
    assert mode_state.state == "off"

    command_state = hass.states.get("sensor.office_last_command")
    assert command_state.state == "disable"

    # 8. Explicitly re-enable switch -> mode returns to auto-off (since lights are off)
    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.schedule_office"})
    await hass.async_block_till_done()

    mode_state = hass.states.get("sensor.office_mode")
    assert mode_state.state == "auto-off"

    command_state = hass.states.get("sensor.office_last_command")
    assert command_state.state == "enable"

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_diagnostic_entities_with_curves(hass: HomeAssistant) -> None:
    """Test dim-to-warm and brightness curve binary sensors with configured curves."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kitchen",
        data={
            CONF_NAME: "kitchen",
            CONF_LIGHTS: ["light.kitchen_spot"],
            CONF_CURVES: {
                "warm_spots": {
                    "lights": ["light.kitchen_spot"],
                    "curve": [
                        {"brightness": 1, "temp": 2000},
                        {"brightness": 100, "temp": 4000},
                    ],
                }
            },
            CONF_BRIGHTNESS_CURVES: {
                "spot_dist": {
                    "lights": ["light.kitchen_spot"],
                    "points": [[0, 0], [100, 100]],
                }
            },
            CONF_SCHEDULE: [
                {"time": "08:00", "brightness": 100},
            ],
        },
    )
    entry.add_to_hass(hass)
    hass.states.async_set("light.kitchen_spot", "on")

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    dtw_sensor = hass.states.get("binary_sensor.kitchen_dim_to_warm_in_use")
    assert dtw_sensor is not None
    assert dtw_sensor.state == "on"
    assert "warm_spots" in dtw_sensor.attributes["curves"]
    assert "light.kitchen_spot" in dtw_sensor.attributes["lights"]
    assert "light.kitchen_spot" in dtw_sensor.attributes["active_lights_on"]

    b_curve_sensor = hass.states.get("binary_sensor.kitchen_brightness_curve_in_use")
    assert b_curve_sensor is not None
    assert b_curve_sensor.state == "on"
    assert "spot_dist" in b_curve_sensor.attributes["curves"]
    assert "light.kitchen_spot" in b_curve_sensor.attributes["lights"]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_problem_binary_sensor_on_unavailable_light(hass: HomeAssistant) -> None:
    """Test problem binary sensor triggers when light entity is unavailable."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Office",
        data={
            CONF_NAME: "office",
            CONF_LIGHTS: ["light.office"],
            CONF_SCHEDULE: [
                {"time": "08:00", "brightness": 100, "temp": 4000},
            ],
        },
    )
    entry.add_to_hass(hass)

    # Missing state in hass -> unavailable
    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    problem_state = hass.states.get("binary_sensor.office_problem")
    assert problem_state is not None
    assert problem_state.state == "on"
    assert "light.office" in problem_state.attributes["unavailable_lights"]

    # Now make the light available (off)
    hass.states.async_set("light.office", "off")
    await hass.async_block_till_done()

    # Trigger program check
    program: ScheduledSceneProgram = hass.data[DOMAIN][entry.entry_id]
    program._notify_listeners()
    await hass.async_block_till_done()

    problem_state = hass.states.get("binary_sensor.office_problem")
    assert problem_state.state == "off"
    assert problem_state.attributes["unavailable_lights"] == []

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_device_registry_grouping(hass: HomeAssistant) -> None:
    """Test all room entities link to the unified device in DeviceRegistry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room",
        data={
            CONF_NAME: "living_room",
            CONF_LIGHTS: ["light.lr_main"],
            CONF_SCHEDULE: [
                {"time": "08:00", "brightness": 100, "temp": 4000},
            ],
        },
    )
    entry.add_to_hass(hass)
    hass.states.async_set("light.lr_main", "off")

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)})
    assert device is not None
    assert device.name == "Living Room"
    assert device.manufacturer == "Scheduled Scenes"

    entity_registry = er.async_get(hass)
    expected_entities = [
        "switch.schedule_living_room",
        "sensor.living_room_schedule_phase",
        "sensor.living_room_mode",
        "sensor.living_room_current_brightness",
        "sensor.living_room_last_command",
        "binary_sensor.living_room_dim_to_warm_in_use",
        "binary_sensor.living_room_brightness_curve_in_use",
        "binary_sensor.living_room_problem",
    ]

    for ent_id in expected_entities:
        reg_entry = entity_registry.async_get(ent_id)
        assert reg_entry is not None, f"Entity {ent_id} not registered in entity registry"
        assert reg_entry.device_id == device.id

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
