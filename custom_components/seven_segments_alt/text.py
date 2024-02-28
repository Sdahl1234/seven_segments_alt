"""Support for SS."""

from __future__ import annotations

import logging

from homeassistant.components.text import TextEntity
from homeassistant.core import HomeAssistant

from . import SSDataCoordinator
from .const import DOMAIN
from .entity import SSEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Do setup entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SSText(coordinator, "extra_arguments", "ss_extra_arguments")])


#     async_add_entities([SSText(coordinator, "camera_entity_id", "ss_camera_entity_id")])


class SSText(SSEntity, TextEntity):
    """SS text."""

    def __init__(
        self,
        coordinator: SSDataCoordinator,
        name: str,
        translationkey: str,
    ) -> None:
        """Init."""
        super().__init__(coordinator)
        self.data_coordinator = coordinator
        self._attr_translation_key = translationkey
        self._attr_has_entity_name = True
        self._tk = translationkey
        self._attr_unique_id = f"{name}_{self.data_coordinator.componentname}"
        self.mode = "text"
        self.jname = name

    async def async_set_value(self, value: str) -> None:
        """Set the text value."""
        self.data_coordinator.jdata[self.jname] = value

    @property
    def native_value(self):
        """Return value."""
        return self.data_coordinator.jdata[self.jname]
