"""Tests for the number platform (brightness offset) of scheduled_scenes."""

from homeassistant.core import HomeAssistant, ServiceCall
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.scheduled_scenes import async_setup
from custom_components.scheduled_scenes.const import (
    CONF_LIGHTS,
    CONF_NAME,
    CONF_SCHEDULE,
    DOMAIN,
)


async def test_brightness_offset_number_entity(hass: HomeAssistant) -> None:
    """Test brightness offset number entity attributes, value changes, and schedule shifts."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room",
        data={
            CONF_NAME: "living_room",
            CONF_LIGHTS: ["light.living_ceiling"],
            CONF_SCHEDULE: [
                {"time": "00:00", "brightness": 50, "temp": 3000},
                {"time": "23:59", "brightness": 50, "temp": 3000},
            ],
        },
    )
    entry.add_to_hass(hass)

    light_calls = []

    async def mock_light_service(call: ServiceCall):
        light_calls.append((call.service, dict(call.data)))

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.services.async_register("light", "turn_on", mock_light_service)
    hass.services.async_register("light", "turn_off", mock_light_service)

    # 1. Verify entity attributes
    offset_state = hass.states.get("number.living_room_brightness_offset")
    assert offset_state is not None
    assert float(offset_state.state) == 0.0
    assert offset_state.attributes["min"] == -50
    assert offset_state.attributes["max"] == 50
    assert offset_state.attributes["step"] == 1
    assert offset_state.attributes["unit_of_measurement"] == "%"

    # Make physical light active (ON)
    hass.states.async_set("light.living_ceiling", "on", {"brightness": 128})
    await hass.async_block_till_done()

    # 2. Adjust offset slider to +20%
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.living_room_brightness_offset", "value": 20},
    )
    await hass.async_block_till_done()

    program = hass.data[DOMAIN][entry.entry_id]
    assert program.brightness_offset == 20
    assert float(hass.states.get("number.living_room_brightness_offset").state) == 20.0

    # Remains in auto mode with adjusted output
    assert program.mode == "auto"

    # Check that transition was dispatched with 50 + 20 = 70% brightness
    last_call = next(c for c in reversed(light_calls) if c[0] == "turn_on")
    assert last_call[1]["brightness_pct"] == 70

    # 3. Adjust offset slider to -30%
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.living_room_brightness_offset", "value": -30},
    )
    await hass.async_block_till_done()

    assert program.brightness_offset == -30
    last_call = next(c for c in reversed(light_calls) if c[0] == "turn_on")
    assert last_call[1]["brightness_pct"] == 20  # 50 - 30 = 20%

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
