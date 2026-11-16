"""Tests for the Studio WebSocket configuration API."""

from unittest.mock import patch

import pytest
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import scheduled_scenes
from custom_components.scheduled_scenes import async_setup
from custom_components.scheduled_scenes.const import (
    CONF_LIGHTS,
    CONF_NAME,
    CONF_SCHEDULE,
    DOMAIN,
)
from custom_components.scheduled_scenes.websocket import get_config, save_config


async def test_get_config_returns_saved_programs(hass: HomeAssistant) -> None:
    """Config retrieval returns persisted programs and shared curves."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Office",
        data={
            CONF_NAME: "office",
            CONF_LIGHTS: ["light.office"],
            CONF_SCHEDULE: [{"time": "07:00", "brightness": 25}],
            "curves": {
                "warm": {"lights": ["light.office"], "curve": [[1, 2000], [100, 4000]]}
            },
            "brightness_curves": {},
        },
    )
    entry.add_to_hass(hass)

    result = get_config(hass)

    assert result["programs"][0]["name"] == "office"
    assert "warm" in result["curves"]


async def test_setup_registers_admin_sidebar_panel(hass: HomeAssistant) -> None:
    """Built panel assets are served and registered for administrators."""
    assert await async_setup_component(hass, "http", {})

    with patch.object(
        scheduled_scenes.frontend, "async_register_built_in_panel"
    ) as register_panel:
        assert await async_setup(hass, {})

    register_panel.assert_called_once()
    assert register_panel.call_args.kwargs["require_admin"] is True
    assert register_panel.call_args.kwargs["frontend_url_path"] == "scheduled-scenes"


async def test_save_config_updates_entry_and_rejects_invalid_schedule(
    hass: HomeAssistant,
) -> None:
    """Saving validates schedule data before updating and reloading entries."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Office",
        data={
            CONF_NAME: "office",
            CONF_LIGHTS: ["light.office"],
            CONF_SCHEDULE: [{"time": "07:00", "brightness": 20}],
        },
    )
    entry.add_to_hass(hass)
    payload = {
        "programs": [
            {
                "name": "office",
                "lights": ["light.office"],
                "schedule": [
                    {"time": "07:00", "brightness": 25},
                    {"time": "22:00", "brightness": 10},
                ],
            }
        ],
        "curves": {},
        "brightness_curves": {},
    }

    with patch.object(hass.config_entries, "async_reload") as reload_entry:
        await save_config(hass, payload)

    assert entry.data[CONF_SCHEDULE][0]["brightness"] == 25
    reload_entry.assert_awaited_once_with(entry.entry_id)
    with pytest.raises(vol.Invalid):
        await save_config(
            hass,
            {**payload, "programs": [{**payload["programs"][0], "schedule": []}]},
        )
    assert entry.data[CONF_SCHEDULE][0]["brightness"] == 25
