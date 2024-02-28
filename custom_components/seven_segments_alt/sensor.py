"""Sensor."""
# import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant

from . import SSDataCoordinator
from .const import DOMAIN
from .entity import SSEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
    """Async Setup entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        [
            ssSensor(
                coordinator,
                "OCR",
                "ss_ocr",
                "mdi:counter",
            )
        ]
    )


class ssSensor(SSEntity, SensorEntity):
    """SS sensor."""

    def __init__(
        self, coordinator: SSDataCoordinator, name: str, translationkey: str, icon: str
    ) -> None:
        """Init."""
        super().__init__(coordinator)
        self.data_coordinator = coordinator
        self._tk = translationkey
        self._attr_translation_key = translationkey
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{name}_{self.data_coordinator.componentname}"
        self._attr_icon = icon

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will reflect this.
    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    @property
    def state(self):  # noqa: C901
        """State."""
        # Hent data fra data_handler her
        return self.data_coordinator.ocr_state
