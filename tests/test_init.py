"""Tests for init lifecycle and YAML configuration."""

from unittest.mock import patch

from homeassistant.core import HomeAssistant, ServiceCall
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.scheduled_scenes import (
    async_reload_entry,
    async_setup,
)
from custom_components.scheduled_scenes.const import (
    ATTR_BRIGHTNESS,
    ATTR_DURATION,
    ATTR_STEP,
    ATTR_TRANSITION,
    CONF_BRIGHTNESS_CURVES,
    CONF_CURVES,
    CONF_LIGHTS,
    CONF_NAME,
    CONF_PROGRAMS,
    CONF_SCHEDULE,
    DOMAIN,
    SERVICE_ADJUST_BRIGHTNESS,
    SERVICE_DISABLE,
    SERVICE_ENABLE,
    SERVICE_RELOAD,
    SERVICE_RESUME_SCHEDULE,
    SERVICE_STEP_BRIGHTNESS,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)


def test_import():
    """The integration package can be imported."""
    from custom_components import scheduled_scenes  # noqa: F401


async def test_async_setup_with_yaml(hass: HomeAssistant) -> None:
    """Test setup from YAML initiates flow."""
    yaml_config = {
        DOMAIN: [
            {
                CONF_NAME: "kitchen",
                CONF_LIGHTS: ["light.kitchen"],
                CONF_SCHEDULE: [
                    {"time": "07:00", "brightness": 80, "temp": 3500},
                    {"time": "21:00", "brightness": 30, "temp": 2700},
                ],
            }
        ]
    }
    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        assert await async_setup(hass, yaml_config)
        await hass.async_block_till_done()
        assert mock_init.called


async def test_async_setup_with_yaml_curves(hass: HomeAssistant) -> None:
    """Test setup from YAML with global curves and programs."""
    yaml_config = {
        DOMAIN: {
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
                "spot_curve": {
                    "lights": ["light.kitchen_spot"],
                    "points": [[0, 0], [100, 100]],
                }
            },
            CONF_PROGRAMS: [
                {
                    CONF_NAME: "kitchen",
                    CONF_LIGHTS: ["light.kitchen_spot"],
                    CONF_SCHEDULE: [
                        {"time": "07:00", "brightness": 50},
                    ],
                }
            ],
        }
    }
    with patch.object(hass.config_entries.flow, "async_init") as mock_init:
        assert await async_setup(hass, yaml_config)
        await hass.async_block_till_done()
        assert mock_init.called
        call_args = mock_init.call_args[1]
        assert call_args["data"][CONF_CURVES]["warm_spots"]["lights"] == [
            "light.kitchen_spot"
        ]
        assert call_args["data"][CONF_BRIGHTNESS_CURVES]["spot_curve"]["lights"] == [
            "light.kitchen_spot"
        ]


async def test_domain_services_and_legacy_aliases(hass: HomeAssistant) -> None:
    """Test domain services with params and program aliases."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bedroom",
        data={
            CONF_NAME: "bedroom",
            CONF_LIGHTS: ["light.bedroom"],
            CONF_SCHEDULE: [
                {"time": "07:00", "brightness": 50, "temp": 3000},
                {"time": "22:00", "brightness": 10, "temp": 2200},
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

    # Domain turn_on with transition
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TURN_ON,
        {"entity_id": "switch.schedule_bedroom", ATTR_TRANSITION: 2.5},
    )
    await hass.async_block_till_done()

    # Domain turn_off with transition
    await hass.services.async_call(
        DOMAIN,
        SERVICE_TURN_OFF,
        {"entity_id": "switch.schedule_bedroom", ATTR_TRANSITION: 1.5},
    )
    await hass.async_block_till_done()

    # Domain disable with duration
    await hass.services.async_call(
        DOMAIN,
        SERVICE_DISABLE,
        {"entity_id": "switch.schedule_bedroom", ATTR_DURATION: 10},
    )
    await hass.async_block_till_done()

    # Domain enable
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ENABLE,
        {"entity_id": "switch.schedule_bedroom"},
    )
    await hass.async_block_till_done()

    # Domain adjust_brightness
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ADJUST_BRIGHTNESS,
        {"entity_id": "switch.schedule_bedroom", ATTR_STEP: 15, ATTR_TRANSITION: 0.5},
    )
    await hass.async_block_till_done()
    sensor_state = hass.states.get("sensor.bedroom_schedule_phase")
    assert sensor_state.attributes.get("manual_override") is True
    assert sensor_state.attributes.get("manual_brightness") == 15

    # Domain step_brightness alias
    await hass.services.async_call(
        DOMAIN,
        SERVICE_STEP_BRIGHTNESS,
        {"entity_id": "switch.schedule_bedroom", ATTR_STEP: 10},
    )
    await hass.async_block_till_done()
    sensor_state = hass.states.get("sensor.bedroom_schedule_phase")
    assert sensor_state.attributes.get("manual_brightness") == 25

    # Domain resume_schedule
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESUME_SCHEDULE,
        {"entity_id": "switch.schedule_bedroom"},
    )
    await hass.async_block_till_done()
    sensor_state = hass.states.get("sensor.bedroom_schedule_phase")
    assert sensor_state.attributes.get("manual_override") is False
    assert sensor_state.attributes.get("manual_brightness") is None

    # Alias adjust_brightness
    await hass.services.async_call(
        DOMAIN,
        "bedroom_adjust_brightness",
        {ATTR_BRIGHTNESS: 80},
    )
    await hass.async_block_till_done()
    sensor_state = hass.states.get("sensor.bedroom_schedule_phase")
    assert sensor_state.attributes.get("manual_brightness") == 80

    # Alias step_brightness
    await hass.services.async_call(
        DOMAIN,
        "bedroom_step_brightness",
        {ATTR_STEP: -20},
    )
    await hass.async_block_till_done()
    sensor_state = hass.states.get("sensor.bedroom_schedule_phase")
    assert sensor_state.attributes.get("manual_brightness") == 60

    # Alias resume_schedule
    await hass.services.async_call(
        DOMAIN,
        "bedroom_resume_schedule",
        {},
    )
    await hass.async_block_till_done()
    sensor_state = hass.states.get("sensor.bedroom_schedule_phase")
    assert sensor_state.attributes.get("manual_brightness") is None

    # Alias turn_on with transition
    await hass.services.async_call(
        DOMAIN,
        "bedroom_turn_on",
        {ATTR_TRANSITION: 3.0},
    )
    await hass.async_block_till_done()

    # Alias turn_off with transition
    await hass.services.async_call(
        DOMAIN,
        "bedroom_turn_off",
        {ATTR_TRANSITION: 3.0},
    )
    await hass.async_block_till_done()

    # Alias disable with duration
    await hass.services.async_call(
        DOMAIN,
        "bedroom_disable",
        {ATTR_DURATION: 5},
    )
    await hass.async_block_till_done()

    # Alias enable
    await hass.services.async_call(
        DOMAIN,
        "bedroom_enable",
        {},
    )
    await hass.async_block_till_done()

    # Reload entry helper
    with patch.object(hass.config_entries, "async_reload") as mock_reload:
        await async_reload_entry(hass, entry)
        assert mock_reload.called

    # Reload service call
    with patch(
        "custom_components.scheduled_scenes.async_integration_yaml_config",
        return_value=None,
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, {})
        await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
