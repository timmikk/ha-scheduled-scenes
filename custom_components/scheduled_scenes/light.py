"""Light platform for scheduled_scenes integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_TRANSITION,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import ScheduledSceneProgram

DEFAULT_MIN_KELVIN = 2000
DEFAULT_MAX_KELVIN = 6500


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the light platform from a config entry."""
    program: ScheduledSceneProgram = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ScheduledSceneLight(program, entry.entry_id)])


class ScheduledSceneLight(LightEntity):
    """Virtual light entity for a scheduled_scenes room program."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:lightbulb-group"
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}
    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_min_color_temp_kelvin = DEFAULT_MIN_KELVIN
    _attr_max_color_temp_kelvin = DEFAULT_MAX_KELVIN

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize light entity."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"{display_name} Lights"
        self._attr_unique_id = f"scheduled_scenes_{program.name}_lights"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=display_name,
            manufacturer="Scheduled Scenes",
            model="Room Program",
        )

    @property
    def is_on(self) -> bool:
        """Return True if any light in the program is currently on."""
        return self.program.is_any_light_on()

    @property
    def brightness(self) -> int:
        """Return current overall room brightness scaled to 0-255."""
        room_b_pct = self.program.get_current_room_brightness()
        return round((room_b_pct / 100) * 255)

    @property
    def color_temp_kelvin(self) -> int:
        """Return current effective room color temperature in Kelvin."""
        return self.program.get_current_room_color_temp()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "mode": self.program.mode,
            "brightness_pct": self.program.get_current_room_brightness(),
            "brightness_offset": self.program.brightness_offset,
            "lights": self.program.lights,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light, resuming schedule or setting manual brightness/temp."""
        transition: float | None = kwargs.get(ATTR_TRANSITION)
        brightness: int | None = kwargs.get(ATTR_BRIGHTNESS)
        color_temp: int | None = kwargs.get(ATTR_COLOR_TEMP_KELVIN)

        if brightness is None and color_temp is None:
            await self.program.async_turn_on(transition_time=transition)
            return

        if brightness is not None:
            pct = round((brightness / 255) * 100)
            await self.program.async_adjust_brightness(
                brightness=pct,
                transition=transition,
                color_temp=color_temp,
            )
        elif color_temp is not None:
            await self.program.async_set_manual_color_temp(
                kelvin=color_temp,
                transition=transition,
            )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off all lights in the program."""
        transition: float | None = kwargs.get(ATTR_TRANSITION)
        await self.program.async_turn_off(transition_time=transition)

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(self.program.async_add_listener(self.async_write_ha_state))
