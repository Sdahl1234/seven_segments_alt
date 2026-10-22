"""Support for SS."""

import io
import logging

from PIL import Image

from homeassistant.components.image import ImageEntity
from homeassistant.core import HomeAssistant

from . import SSDataCoordinator
from .const import DOMAIN, SS_HEIGHT, SS_WIDTH, SS_X_POS, SS_Y_POS
from .entity import SSEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    """Do setup entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SSImage(hass, coordinator, "SS Image", "ss_image")])
    async_add_entities([SSImage_Pro(hass, coordinator, "SS Image pro", "ss_image_pro")])
    async_add_entities(
        [SSImage_Crop(hass, coordinator, "SS Image crop", "ss_image_crop")]
    )


class SSImage_Crop(SSEntity, ImageEntity):
    """SS Image Pro."""

    data_coordinator: SSDataCoordinator

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: SSDataCoordinator,
        name: str,
        translationkey: str,
    ) -> None:
        """Init."""
        self.hass = hass
        super().__init__(coordinator)
        ImageEntity.__init__(self, hass, False)
        self.data_coordinator = coordinator
        self._attr_translation_key = translationkey
        self._attr_has_entity_name = True
        self._tk = translationkey
        self._attr_unique_id = f"{name}_{self.data_coordinator.componentname}"
        self.jname = name
        self.data_coordinator.image_entity_3 = self

    def _crop_image(self, content: bytes, box: tuple[int, int, int, int]) -> bytes:
        """Crop the camera image and return it as PNG."""
        with Image.open(io.BytesIO(content)) as img:
            roi_img = img.crop(box)
            img_byte_arr = io.BytesIO()
            roi_img.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        try:
            _LOGGER.debug(self.data_coordinator.processed_name)
            jdata = self.data_coordinator.jdata
            box = (
                jdata[SS_X_POS],
                jdata[SS_Y_POS],
                jdata[SS_X_POS] + jdata[SS_WIDTH],
                jdata[SS_Y_POS] + jdata[SS_HEIGHT],
            )
            return await self.hass.async_add_executor_job(
                self._crop_image, self.data_coordinator.ocr_image.content, box
            )
        except Exception as ex:  # pylint: disable=broad-except  # noqa: BLE001
            _LOGGER.debug(ex)
            return None


class SSImage_Pro(SSEntity, ImageEntity):
    """SS Image Pro."""

    data_coordinator: SSDataCoordinator

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: SSDataCoordinator,
        name: str,
        translationkey: str,
    ) -> None:
        """Init."""
        self.hass = hass
        super().__init__(coordinator)
        ImageEntity.__init__(self, hass, False)
        self.data_coordinator = coordinator
        self._attr_translation_key = translationkey
        self._attr_has_entity_name = True
        self._tk = translationkey
        self._attr_unique_id = f"{name}_{self.data_coordinator.componentname}"
        self.jname = name
        self.data_coordinator.image_entity = self

    def _convert_image(self, path) -> bytes:
        """Convert the processed image file to RGB PNG."""
        with Image.open(path, "r") as img:
            roi_img = img.convert("RGB")
            img_byte_arr = io.BytesIO()
            roi_img.save(img_byte_arr, format="PNG")
        return img_byte_arr.getvalue()

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        try:
            _LOGGER.debug(self.data_coordinator.processed_name)
            return await self.hass.async_add_executor_job(
                self._convert_image, self.data_coordinator.processed_name
            )
        except Exception as ex:  # pylint: disable=broad-except  # noqa: BLE001
            _LOGGER.debug(ex)
            return None


class SSImage(SSEntity, ImageEntity):
    """SS Image."""

    data_coordinator: SSDataCoordinator

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: SSDataCoordinator,
        name: str,
        translationkey: str,
    ) -> None:
        """Init."""
        self.hass = hass
        super().__init__(coordinator)
        ImageEntity.__init__(self, hass, False)
        self.data_coordinator = coordinator
        self._attr_translation_key = translationkey
        self._attr_has_entity_name = True
        self._tk = translationkey
        self._attr_unique_id = f"{name}_{self.data_coordinator.componentname}"
        self.jname = name
        self.data_coordinator.image_entity_2 = self

    async def async_image(self) -> bytes | None:
        """Return bytes of image."""
        try:
            _LOGGER.debug("New ss image")
            return self.data_coordinator.ocr_image.content  # noqa: TRY300
        except Exception as ex:  # pylint: disable=broad-except  # noqa: BLE001
            _LOGGER.debug(ex)
            return None
