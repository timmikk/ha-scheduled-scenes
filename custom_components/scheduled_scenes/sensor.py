"""Diagnostic sensor platform for scheduled_scenes integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ScheduledSceneProgram


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform from a config entry."""
    program: ScheduledSceneProgram = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ScheduledSceneSensor(program, entry.entry_id)])


class ScheduledSceneSensor(SensorEntity):
    """Sensor showing current schedule phase and target values."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clock-outline"

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize sensor entity."""
        self.program = program
        self._entry_id = entry_id

        self._attr_name = f"{program.name.title()} Schedule Phase"
        self._attr_unique_id = f"scheduled_scenes_{program.name}_phase"

    @property
    def native_value(self) -> str:
        """Return the current schedule interval phase as state."""
        t = self.program.current_transition
        if t is None:
            return "idle"
        return f"{t.start_step.time.strftime('%H:%M')}-{t.end_step.time.strftime('%H:%M')}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostic schedule attributes."""
        attrs: dict[str, Any] = {
            "enabled": self.program.enabled,
            "lights": self.program.lights,
            "any_light_on": self.program.is_any_light_on(),
        }
        t = self.program.current_transition
        if t is not None:
            attrs.update(
                {
                    "start_time": t.start_step.time.strftime("%H:%M"),
                    "end_time": t.end_step.time.strftime("%H:%M"),
                    "start_brightness": t.start_step.brightness,
                    "end_brightness": t.end_step.brightness,
                    "start_temp": t.start_step.temp,
                    "end_temp": t.end_step.temp,
                }
            )
        return attrs

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(
            self.program.async_add_listener(self.async_write_ha_state)
        )
