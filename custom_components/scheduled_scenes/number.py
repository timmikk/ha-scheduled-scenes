"""Number platform for scheduled_scenes integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
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
    """Set up the number platform from a config entry."""
    program: ScheduledSceneProgram = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ScheduledSceneBrightnessOffsetNumber(program, entry.entry_id)])


class ScheduledSceneBrightnessOffsetNumber(NumberEntity):
    """Number slider for adjusting schedule brightness offset."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:brightness-percent"
    _attr_native_min_value = -50
    _attr_native_max_value = 50
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize number entity."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"{display_name} Brightness Offset"
        self._attr_unique_id = f"scheduled_scenes_{program.name}_brightness_offset"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=display_name,
            manufacturer="Scheduled Scenes",
            model="Room Program",
        )

    @property
    def native_value(self) -> float:
        """Return current brightness offset."""
        return float(self.program.brightness_offset)

    async def async_set_native_value(self, value: float) -> None:
        """Update brightness offset."""
        await self.program.async_set_brightness_offset(int(value))

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(self.program.async_add_listener(self.async_write_ha_state))
