"""Tests for the scheduled_scenes config flow and options flow."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.scheduled_scenes.const import (
    CONF_ALLOW_TURN_ON_IF_ANY_ON,
    CONF_BRIGHTNESS_CURVES,
    CONF_CURVES,
    CONF_DISABLE_WHEN_LIGHTS_OFF,
    CONF_ENABLE_WHEN_LIGHT_TURN_ON,
    CONF_LIGHTS,
    CONF_NAME,
    CONF_SCHEDULE,
    CONF_TRANSITION_INTERVAL,
    CONF_TRANSITION_TIME,
    CONF_TRANSITION_TIME_ON,
    CONF_TRANSITION_TIME_ON_LIGHT_TURN_ON,
    DOMAIN,
)


async def test_config_flow_happy_path(hass: HomeAssistant) -> None:
    """Test standard user config flow creating a valid entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    schedule_yaml = """
- time: "06:00"
  brightness: 20
  temp: 2200
- time: "12:00"
  brightness: 100
  temp: 4500
"""
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "living_room",
            CONF_LIGHTS: ["light.ceiling"],
            CONF_SCHEDULE: schedule_yaml,
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Living_Room"
    assert result2["data"][CONF_NAME] == "living_room"
    assert len(result2["data"][CONF_SCHEDULE]) == 2


async def test_config_flow_with_curves(hass: HomeAssistant) -> None:
    """Test config flow with dim-to-warm curves YAML."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    schedule_yaml = """
- time: "07:00"
  brightness: 30
- time: "19:00"
  brightness: 80
"""
    curves_yaml = """
warm_glow:
  lights:
    - light.spot_1
  curve:
    - [1, 2000]
    - [100, 4000]
"""
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "dining_room",
            CONF_LIGHTS: ["light.spot_1"],
            CONF_SCHEDULE: schedule_yaml,
            CONF_CURVES: curves_yaml,
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert CONF_CURVES in result2["data"]
    assert "warm_glow" in result2["data"][CONF_CURVES]


async def test_config_flow_invalid_curves(hass: HomeAssistant) -> None:
    """Test config flow with malformed curves YAML."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "dining_room",
            CONF_LIGHTS: ["light.spot_1"],
            CONF_SCHEDULE: "- time: '08:00'\n  brightness: 100\n",
            CONF_CURVES: "not: a: [valid, yaml: {",
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_CURVES] == "invalid_curves"


async def test_config_flow_invalid_schedule(hass: HomeAssistant) -> None:
    """Test user flow with broken schedule YAML."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "test_room",
            CONF_LIGHTS: ["light.lamp"],
            CONF_SCHEDULE: "not: a: list:",
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_SCHEDULE] == "invalid_schedule"


async def test_config_flow_already_configured(hass: HomeAssistant) -> None:
    """Test duplicate room name aborts flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={CONF_NAME: "bedroom", CONF_LIGHTS: ["light.bed"], CONF_SCHEDULE: []},
        unique_id="bedroom",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "bedroom",
            CONF_LIGHTS: ["light.bed"],
            CONF_SCHEDULE: "- time: '08:00'\n  brightness: 100\n  temp: 3000\n",
        },
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test updating schedule and curves via options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Kitchen",
        data={
            CONF_NAME: "kitchen",
            CONF_LIGHTS: ["light.kitchen"],
            CONF_SCHEDULE: [{"time": "08:00", "brightness": 100, "temp": 3000}],
        },
        unique_id="kitchen",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    new_schedule = """
- time: "07:00"
  brightness: 50
- time: "19:00"
  brightness: 80
"""
    new_curves = """
spots:
  lights: [light.kitchen]
  curve: [[1, 2200], [100, 3800]]
"""
    new_b_curves = """
accent:
  lights: [light.island]
  points: [[0, 0], [50, 100], [100, 100]]
"""
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_LIGHTS: ["light.kitchen", "light.island"],
            CONF_SCHEDULE: new_schedule,
            CONF_CURVES: new_curves,
            CONF_BRIGHTNESS_CURVES: new_b_curves,
            CONF_TRANSITION_TIME: 60,
            CONF_TRANSITION_INTERVAL: 60,
            CONF_TRANSITION_TIME_ON_LIGHT_TURN_ON: 0.5,
            CONF_TRANSITION_TIME_ON: 0.5,
            CONF_ENABLE_WHEN_LIGHT_TURN_ON: True,
            CONF_DISABLE_WHEN_LIGHTS_OFF: True,
            CONF_ALLOW_TURN_ON_IF_ANY_ON: False,
        },
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert len(result2["data"][CONF_SCHEDULE]) == 2
    assert "spots" in result2["data"][CONF_CURVES]
    assert "accent" in result2["data"][CONF_BRIGHTNESS_CURVES]

async def test_config_flow_import_success(hass: HomeAssistant) -> None:
    """Test successful YAML import flow."""
    import_data = {
        CONF_NAME: "patio",
        CONF_LIGHTS: ["light.patio"],
        CONF_SCHEDULE: [
            {"time": "08:00", "brightness": 100, "temp": 3000},
            {"time": "20:00", "brightness": 50, "temp": 2500},
        ],
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=import_data,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Patio"


async def test_config_flow_import_duplicate_updates(hass: HomeAssistant) -> None:
    """Test importing an existing entry updates it and aborts."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Patio",
        data={CONF_NAME: "patio", CONF_LIGHTS: ["light.patio"], CONF_SCHEDULE: []},
    )
    entry.add_to_hass(hass)

    import_data = {
        CONF_NAME: "patio",
        CONF_LIGHTS: ["light.patio_2"],
        CONF_SCHEDULE: [
            {"time": "09:00", "brightness": 80, "temp": 3200},
        ],
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=import_data,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_config_flow_import_invalid_schedule(hass: HomeAssistant) -> None:
    """Test importing with invalid schedule aborts."""
    import_data = {
        CONF_NAME: "bad_room",
        CONF_LIGHTS: ["light.bad"],
        CONF_SCHEDULE: [],
    }
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data=import_data,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "invalid_schedule"


async def test_config_flow_empty_string_or_list_schedule(hass: HomeAssistant) -> None:
    """Test empty schedule string or list returns validation error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "empty_schedule",
            CONF_LIGHTS: ["light.lamp"],
            CONF_SCHEDULE: "[]",
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"][CONF_SCHEDULE] == "invalid_schedule"
