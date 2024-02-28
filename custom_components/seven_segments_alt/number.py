"""Support for SS."""

from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant

from . import SSDataCoordinator
from .const import DOMAIN
from .entity import SSEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Do setup entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([SSNumber(coordinator, "x_position", "ss_x_position")])
    async_add_entities([SSNumber(coordinator, "y_position", "ss_y_position")])
    async_add_entities([SSNumber(coordinator, "height", "ss_height")])
    async_add_entities([SSNumber(coordinator, "width", "ss_width")])
    async_add_entities([SSNumber(coordinator, "rotate", "ss_rotate")])
    async_add_entities([SSNumber(coordinator, "threshold", "ss_threshold")])
    async_add_entities([SSNumber(coordinator, "digits", "ss_digits")])


class SSNumber(SSEntity, NumberEntity):
    """SS number."""

    def __init__(
        self,
        coordinator: SSDataCoordinator,
        name: str,
        translationkey: str,
    ) -> None:
        """Init."""
        super().__init__(coordinator)
        self.data_coordinator = coordinator
        self.jname = name
        self.native_step = 1
        self.native_max_value = 5000
        self.native_min_value = -100
        self.mode = NumberMode.BOX
        self._attr_translation_key = translationkey
        self._attr_has_entity_name = True
        self._tk = translationkey
        self._attr_unique_id = f"{name}_{self.data_coordinator.componentname}"

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self.data_coordinator.jdata[self.jname] = int(value)
        await self.data_coordinator.ocr_entity.set_command()

    @property
    def native_value(self):
        """Return value."""
        return self.data_coordinator.jdata[self.jname]
