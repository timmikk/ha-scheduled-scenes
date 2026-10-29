"""Diagnostic binary sensor platform for scheduled_scenes integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
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
    """Set up the binary_sensor platform from a config entry."""
    program: ScheduledSceneProgram = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ScheduledSceneDimToWarmBinarySensor(program, entry.entry_id),
            ScheduledSceneBrightnessCurveBinarySensor(program, entry.entry_id),
            ScheduledSceneProblemBinarySensor(program, entry.entry_id),
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


class ScheduledSceneDimToWarmBinarySensor(BinarySensorEntity):
    """Diagnostic binary sensor indicating whether dim-to-warm curves are active."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:sun-thermometer"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize dim-to-warm binary sensor."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"{display_name} Dim-to-Warm In Use"
        self._attr_unique_id = f"scheduled_scenes_{program.name}_dim_to_warm_in_use"
        self._attr_device_info = _build_device_info(program, entry_id)

    @property
    def is_on(self) -> bool:
        """Return True if dim-to-warm curves are configured."""
        return self.program.is_dim_to_warm_in_use

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return dim-to-warm curve details."""
        return {
            "configured": bool(self.program.light_curves),
            "curves": list(self.program.curves.keys()),
            "lights": list(self.program.light_curves.keys()),
            "active_lights_on": [
                lt for lt in self.program.light_curves if self.program.is_light_on(lt)
            ],
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(self.program.async_add_listener(self.async_write_ha_state))


class ScheduledSceneBrightnessCurveBinarySensor(BinarySensorEntity):
    """Diagnostic binary sensor indicating whether brightness curves are active."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:chart-bell-curve"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize brightness curve binary sensor."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"{display_name} Brightness Curve In Use"
        self._attr_unique_id = (
            f"scheduled_scenes_{program.name}_brightness_curve_in_use"
        )
        self._attr_device_info = _build_device_info(program, entry_id)

    @property
    def is_on(self) -> bool:
        """Return True if brightness curves are configured."""
        return self.program.is_brightness_curve_in_use

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return brightness curve details."""
        return {
            "configured": bool(self.program.light_brightness_curves),
            "curves": list(self.program.brightness_curves.keys()),
            "lights": list(self.program.light_brightness_curves.keys()),
            "active_lights_on": [
                lt
                for lt in self.program.light_brightness_curves
                if self.program.is_light_on(lt)
            ],
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(self.program.async_add_listener(self.async_write_ha_state))


class ScheduledSceneProblemBinarySensor(BinarySensorEntity):
    """Diagnostic problem binary sensor indicating missing lights or runtime errors."""

    _attr_has_entity_name = False
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, program: ScheduledSceneProgram, entry_id: str) -> None:
        """Initialize problem binary sensor."""
        self.program = program
        self._entry_id = entry_id

        display_name = program.name.replace("_", " ").title()
        self._attr_name = f"{display_name} Problem"
        self._attr_unique_id = f"scheduled_scenes_{program.name}_problem"
        self._attr_device_info = _build_device_info(program, entry_id)

    @property
    def is_on(self) -> bool:
        """Return True if problem detected."""
        return self.program.is_problem

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return problem diagnostic details."""
        ts = self.program.last_error_timestamp
        return {
            "unavailable_lights": self.program.get_unavailable_lights(),
            "last_error": self.program.last_error,
            "last_error_timestamp": ts.isoformat() if ts is not None else None,
            "error_count": self.program.error_count,
        }

    async def async_added_to_hass(self) -> None:
        """Subscribe to program state changes."""
        self.async_on_remove(self.program.async_add_listener(self.async_write_ha_state))
