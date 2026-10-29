"""Switch platform for scheduled_scenes integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ScheduledSceneProgram


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform from a config entry."""
    program: ScheduledSceneProgram = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ScheduledSceneSwitch(program, entry.entry_id)])


class ScheduledSceneSwitch(SwitchEntity):
    """Switch representation of a scheduled_scenes program."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize switch entity."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"Schedule {display_name}"
        self._attr_unique_id = f"scheduled_scenes_{program.name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=display_name,
            manufacturer="Scheduled Scenes",
            model="Room Program",
        )

    @property
    def is_on(self) -> bool:
        """Return True if schedule transitions are currently enabled."""
        return self.program.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable schedule transitions."""
        self.program.set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable schedule transitions."""
        self.program.set_enabled(False)

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(self.program.async_add_listener(self.async_write_ha_state))
