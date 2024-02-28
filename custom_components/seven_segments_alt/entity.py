"""Base SS entity."""
from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SSDataCoordinator


class SSEntity(CoordinatorEntity[SSDataCoordinator]):
    """Base SS entity."""

    def __init__(
        self,
        coordinator: SSDataCoordinator,
    ) -> None:
        """Initialize light."""
        super().__init__(coordinator)
        self._attr_has_entity_name = False
        self._attr_device_info = coordinator.device_info

        self._attr_unique_id = (
            f"{coordinator.unique_id}-{self.__class__.__name__.lower()}"
        )
