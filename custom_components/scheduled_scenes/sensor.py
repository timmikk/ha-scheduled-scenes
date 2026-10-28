"""Sensor platform for scheduled_scenes integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
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
    """Set up the sensor platform from a config entry."""
    program: ScheduledSceneProgram = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ScheduledSceneSensor(program, entry.entry_id),
            ScheduledSceneModeSensor(program, entry.entry_id),
            ScheduledSceneBrightnessSensor(program, entry.entry_id),
            ScheduledSceneLastCommandSensor(program, entry.entry_id),
        ]
    )


def _build_device_info(program: ScheduledSceneProgram, entry_id: str) -> DeviceInfo:
    """Build device info linking entities for this program."""
    display_name = program.name.replace("_", " ").title()
    return DeviceInfo(
        identifiers={(DOMAIN, entry_id)},
        name=display_name,
        manufacturer="Scheduled Scenes",
        model="Room Program",
    )


class ScheduledSceneSensor(SensorEntity):
    """Sensor showing current schedule phase and target values."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:clock-outline"

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize sensor entity."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"{display_name} Schedule Phase"
        self._attr_unique_id = f"scheduled_scenes_{program.name}_phase"
        self._attr_device_info = _build_device_info(program, entry_id)

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
            "mode": self.program.mode,
            "lights": self.program.lights,
            "any_light_on": self.program.is_any_light_on(),
            "manual_override": self.program.manual_brightness is not None,
            "manual_brightness": self.program.manual_brightness,
            "current_brightness": self.program.get_current_room_brightness(),
            "last_command": self.program.last_command,
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


class ScheduledSceneModeSensor(SensorEntity):
    """Sensor reporting current operational mode (off / auto-off / auto / manual)."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:tune-vertical"

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize mode sensor."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"{display_name} Mode"
        self._attr_unique_id = f"scheduled_scenes_{program.name}_mode"
        self._attr_device_info = _build_device_info(program, entry_id)

    @property
    def native_value(self) -> str:
        """Return the current operational mode."""
        return self.program.mode

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return mode attributes."""
        return {
            "enabled": self.program.enabled,
            "manual_override": self.program.manual_brightness is not None,
            "manual_brightness": self.program.manual_brightness,
            "auto_disabled": self.program._auto_disabled_by_lights_off,
            "any_light_on": self.program.is_any_light_on(),
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(
            self.program.async_add_listener(self.async_write_ha_state)
        )


class ScheduledSceneBrightnessSensor(SensorEntity):
    """Sensor reporting current room brightness percentage."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:brightness-6"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize brightness sensor."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"{display_name} Current Brightness"
        self._attr_unique_id = f"scheduled_scenes_{program.name}_current_brightness"
        self._attr_device_info = _build_device_info(program, entry_id)

    @property
    def native_value(self) -> int:
        """Return the current room brightness (0-100%)."""
        return self.program.get_current_room_brightness()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed brightness attributes."""
        light_b_dict: dict[str, int] = {}
        for light_id in self.program.lights:
            st = self.program.hass.states.get(light_id)
            if st is not None and st.state == "on":
                raw_b = st.attributes.get("brightness")
                if raw_b is not None:
                    light_b_dict[light_id] = round((int(raw_b) / 255) * 100)
                else:
                    light_b_dict[light_id] = 100

        return {
            "manual_brightness": self.program.manual_brightness,
            "is_brightness_curve_in_use": self.program.is_brightness_curve_in_use,
            "light_brightnesses": light_b_dict,
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(
            self.program.async_add_listener(self.async_write_ha_state)
        )


class ScheduledSceneLastCommandSensor(SensorEntity):
    """Diagnostic sensor reporting the last command executed for this room."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:history"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize last command sensor."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"{display_name} Last Command"
        self._attr_unique_id = f"scheduled_scenes_{program.name}_last_command"
        self._attr_device_info = _build_device_info(program, entry_id)

    @property
    def native_value(self) -> str:
        """Return the last command executed."""
        return self.program.last_command

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return command timestamp and execution details."""
        ts = self.program.last_command_timestamp
        return {
            "timestamp": ts.isoformat() if ts is not None else None,
            "details": self.program.last_command_details,
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(
            self.program.async_add_listener(self.async_write_ha_state)
        )
