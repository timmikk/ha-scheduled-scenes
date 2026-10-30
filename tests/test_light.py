"""Tests for the virtual light platform of scheduled_scenes."""

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_TRANSITION,
    ColorMode,
)
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.scheduled_scenes import async_setup
from custom_components.scheduled_scenes.const import (
    CONF_CURVES,
    CONF_LIGHTS,
    CONF_NAME,
    CONF_SCHEDULE,
    DOMAIN,
)


async def test_virtual_light_setup_and_attributes(hass: HomeAssistant) -> None:
    """Test virtual light entity registration, naming, and properties."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Living Room",
        data={
            CONF_NAME: "living_room",
            CONF_LIGHTS: ["light.living_ceiling"],
            CONF_SCHEDULE: [
                {"time": "08:00", "brightness": 60, "temp": 3500},
                {"time": "20:00", "brightness": 40, "temp": 2500},
            ],
        },
    )
    entry.add_to_hass(hass)

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    light_state = hass.states.get("light.living_room_lights")
    assert light_state is not None
    assert light_state.name == "Living Room Lights"
    assert light_state.state == "off"
    assert light_state.attributes["supported_color_modes"] == [ColorMode.COLOR_TEMP]
    assert light_state.attributes["mode"] == "auto-off"
    assert light_state.attributes["brightness_offset"] == 0

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_virtual_light_turn_on_and_off(hass: HomeAssistant) -> None:
    """Test virtual light on/off toggles dispatch to fixtures and restore auto mode."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Study",
        data={
            CONF_NAME: "study",
            CONF_LIGHTS: ["light.study_lamp"],
            CONF_SCHEDULE: [
                {"time": "00:00", "brightness": 70, "temp": 4000},
                {"time": "23:59", "brightness": 70, "temp": 4000},
            ],
        },
    )
    entry.add_to_hass(hass)

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    program = hass.data[DOMAIN][entry.entry_id]
    light_calls = []

    async def mock_call(domain: str, service: str, service_data: dict):
        light_calls.append((service, service_data))

    program._async_call_service = mock_call

    # 1. Turn on via virtual light (no brightness param -> resumes auto schedule)
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.study_lights"},
    )
    await hass.async_block_till_done()

    assert any(
        c[0] == "turn_on" and c[1]["entity_id"] == "light.study_lamp"
        for c in light_calls
    )
    turn_on_call = next(
        c
        for c in light_calls
        if c[0] == "turn_on" and c[1]["entity_id"] == "light.study_lamp"
    )
    assert turn_on_call[1]["brightness_pct"] == 70
    assert turn_on_call[1]["color_temp_kelvin"] == 4000
    assert program.mode in ("auto", "auto-off")
    assert program.manual_brightness is None

    # Simulate physical light reporting ON
    hass.states.async_set(
        "light.study_lamp", "on", {"brightness": 178, "color_temp_kelvin": 4000}
    )
    await hass.async_block_till_done()
    assert hass.states.get("light.study_lights").state == "on"

    # 2. Turn off via virtual light
    light_calls.clear()
    await hass.services.async_call(
        "light",
        "turn_off",
        {"entity_id": "light.study_lights", ATTR_TRANSITION: 1.0},
    )
    await hass.async_block_till_done()

    assert any(
        c[0] == "turn_off" and "light.study_lamp" in c[1]["entity_id"]
        for c in light_calls
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_virtual_light_brightness_slider_without_dim_to_warm(
    hass: HomeAssistant,
) -> None:
    """Test brightness slider pauses schedule and preserves scheduled Kelvin when DTW is off."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Office",
        data={
            CONF_NAME: "office",
            CONF_LIGHTS: ["light.office_desk"],
            CONF_SCHEDULE: [
                {"time": "00:00", "brightness": 100, "temp": 5000},
                {"time": "23:59", "brightness": 100, "temp": 5000},
            ],
        },
    )
    entry.add_to_hass(hass)

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    program = hass.data[DOMAIN][entry.entry_id]
    light_calls = []

    async def mock_call(domain: str, service: str, service_data: dict):
        light_calls.append((service, service_data))

    program._async_call_service = mock_call

    # Initial physical light ON at full scheduled daylight (5000K)
    hass.states.async_set(
        "light.office_desk", "on", {"brightness": 255, "color_temp_kelvin": 5000}
    )
    await hass.async_block_till_done()

    # Move brightness slider to 30% (brightness = 76 out of 255)
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.office_lights", ATTR_BRIGHTNESS: 76},
    )
    await hass.async_block_till_done()

    assert program.mode == "manual"
    assert program.manual_brightness == 30

    # Ensure the brightness changed to 30% while preserving 5000K from schedule
    turn_on_call = next(c for c in reversed(light_calls) if c[0] == "turn_on")
    assert turn_on_call[1]["brightness_pct"] == 30
    assert turn_on_call[1]["color_temp_kelvin"] == 5000

    # Turning on without brightness resumes auto schedule
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.office_lights"},
    )
    await hass.async_block_till_done()
    assert program.mode == "auto"
    assert program.manual_brightness is None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_virtual_light_dim_to_warm_and_manual_kelvin(hass: HomeAssistant) -> None:
    """Test dim-to-warm evaluation on slider and manual color temp override."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Lounge",
        data={
            CONF_NAME: "lounge",
            CONF_LIGHTS: ["light.lounge_spot"],
            CONF_CURVES: {
                "lounge_dtw": {
                    "lights": ["light.lounge_spot"],
                    "points": [[1, 2200], [50, 2700], [100, 4000]],
                }
            },
            CONF_SCHEDULE: [
                {"time": "00:00", "brightness": 80},
                {"time": "23:59", "brightness": 80},
            ],
        },
    )
    entry.add_to_hass(hass)

    assert await async_setup(hass, {})
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    program = hass.data[DOMAIN][entry.entry_id]
    light_calls = []

    async def mock_call(domain: str, service: str, service_data: dict):
        light_calls.append((service, service_data))

    program._async_call_service = mock_call

    hass.states.async_set(
        "light.lounge_spot", "on", {"brightness": 204, "color_temp_kelvin": 3500}
    )
    await hass.async_block_till_done()

    # 1. Slider to 50% -> Dim-to-warm curve evaluates to 2700K
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.lounge_lights", ATTR_BRIGHTNESS: 128},
    )
    await hass.async_block_till_done()

    call_50 = next(c for c in reversed(light_calls) if c[0] == "turn_on")
    assert call_50[1]["brightness_pct"] == 50
    assert call_50[1]["color_temp_kelvin"] == 2700

    # 2. Manual Color Temperature override to 2200K
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.lounge_lights", ATTR_COLOR_TEMP_KELVIN: 2200},
    )
    await hass.async_block_till_done()

    assert program.manual_color_temp == 2200
    assert program.mode == "manual"

    call_temp = next(c for c in reversed(light_calls) if c[0] == "turn_on")
    assert call_temp[1]["color_temp_kelvin"] == 2200

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
