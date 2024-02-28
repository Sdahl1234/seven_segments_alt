"""Support for SS."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant

from . import SSDataCoordinator
from .const import DOMAIN
from .entity import SSEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Do setup entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SSButton(coordinator, "Save data", "ss_save_data")])
    async_add_entities([SSButton(coordinator, "Load data", "ss_load_data")])


class SSButton(SSEntity, ButtonEntity):
    """SS buttons."""

    data_coordinator: SSDataCoordinator

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
        self._attr_unique_id = f"{name}_{self.data_coordinator.componentname}"
        self._attr_has_entity_name = True
        self.mode = "text"
        self._tk = translationkey
        self.jname = name
        # self._attr_unique_id = (
        #     f"{DOMAIN}_{self.data_coordinator.componentname}_{self._tk}"
        # )

    async def async_press(self) -> None:
        """Handle the button press."""
        if self._tk == "ss_save_data":
            await self.data_coordinator.save_data(True)
            await self.data_coordinator.ocr_entity.set_command()
        elif self._tk == "ss_load_data":
            await self.data_coordinator.load_data()
            await self.data_coordinator.ocr_entity.set_command()
