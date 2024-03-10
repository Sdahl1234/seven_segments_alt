"""Optical character recognition processing of seven segments displays."""
from __future__ import annotations

import io
import logging
import os
import subprocess

from PIL import Image

from homeassistant.components.camera import async_get_image
from homeassistant.components.image_processing import (
    ImageProcessingDeviceClass,
    ImageProcessingEntity,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import SSDataCoordinator
from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    SS_DIGITS,
    SS_EXTRA_ARGUMENTS,
    SS_HEIGHT,
    SS_ROTATE,
    SS_THRESHOLD,
    SS_WIDTH,
    SS_X_POS,
    SS_Y_POS,
)
from .entity import SSEntity

_LOGGER = logging.getLogger(__name__)


DEFAULT_BINARY = "ssocr"


# async def async_setup_entry(hass: HomeAssistant, entry, async_add_devices):
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Seven segments OCR platform."""
    coordinator: SSDataCoordinator = hass.data[DOMAIN][DATA_COORDINATOR]
    entities = []
    entities.append(
        ImageProcessingSsocr(
            hass, coordinator.camera_entity_id, coordinator, "img_ssocr", "ss_img_ssocr"
        )
    )
    async_add_entities(entities)


class ImageProcessingSsocr(SSEntity, ImageProcessingEntity):
    """Representation of the seven segments OCR image processing entity."""

    _attr_device_class = ImageProcessingDeviceClass.OCR

    def __init__(
        self,
        hass: HomeAssistant,
        camera_entity,
        coordinator: SSDataCoordinator,
        name,
        translationkey,
    ) -> None:
        """Initialize seven segments processing."""
        super().__init__(coordinator)
        self.hass = hass
        self.data_coordinator: SSDataCoordinator = coordinator
        self._attr_translation_key = translationkey
        self._attr_has_entity_name = True
        self._tk = translationkey
        self._attr_unique_id = f"{name}_{self.data_coordinator.componentname}"

        self._camera_entity = camera_entity
        self._state = None
        self.data_coordinator.ocr_entity = self
        self._attr_device_class = ImageProcessingDeviceClass.OCR

        self.filepath = os.path.join(
            self.hass.config.config_dir,
            "ssocr-{}.png".format(
                (self.data_coordinator.componentname + "_" + name).replace(" ", "_")
            ),
        )
        self.data_coordinator.img_path = self.filepath
        crop = [
            "crop",
            str(self.data_coordinator.jdata[SS_X_POS]),
            str(self.data_coordinator.jdata[SS_Y_POS]),
            str(self.data_coordinator.jdata[SS_WIDTH]),
            str(self.data_coordinator.jdata[SS_HEIGHT]),
        ]
        digits = ["-d", str(self.data_coordinator.jdata[SS_DIGITS])]
        rotate = ["rotate", str(self.data_coordinator.jdata[SS_ROTATE])]
        threshold = ["-t", str(self.data_coordinator.jdata[SS_THRESHOLD])]
        extra_arguments = self.data_coordinator.jdata[SS_EXTRA_ARGUMENTS].split(" ")

        self._command = (
            [DEFAULT_BINARY]
            + crop
            + digits
            + threshold
            + rotate
            + [self.data_coordinator.mandatory_extras]
            + extra_arguments
        )
        self._command.append(self.filepath)
        _LOGGER.debug(self._command)

    async def set_command(self):
        """Update command params."""
        crop = [
            "crop",
            str(self.data_coordinator.jdata[SS_X_POS]),
            str(self.data_coordinator.jdata[SS_Y_POS]),
            str(self.data_coordinator.jdata[SS_WIDTH]),
            str(self.data_coordinator.jdata[SS_HEIGHT]),
        ]
        digits = ["-d", str(self.data_coordinator.jdata[SS_DIGITS])]
        rotate = ["rotate", str(self.data_coordinator.jdata[SS_ROTATE])]
        threshold = ["-t", str(self.data_coordinator.jdata[SS_THRESHOLD])]
        extra_arguments = self.data_coordinator.jdata[SS_EXTRA_ARGUMENTS].split(" ")

        self._command = (
            [DEFAULT_BINARY]
            + crop
            + digits
            + threshold
            + rotate
            + [self.data_coordinator.mandatory_extras]
            + extra_arguments
        )
        self._command.append(self.filepath)
        _LOGGER.debug(self._command)

    @property
    def camera_entity(self):
        """Return camera entity id from process pictures."""
        return self._camera_entity

    @property
    def state(self):
        """Return the state of the entity."""
        return self._state

    async def async_update(self) -> None:
        """Update image and process it.

        This method is a coroutine.
        """
        try:
            image: Image = await async_get_image(
                self.hass, entity_id=self.camera_entity, timeout=self.timeout
            )
            self.data_coordinator.ocr_image = image
            # image_last_updated = datetime.now()
        except HomeAssistantError as err:
            _LOGGER.debug("Error on receive image from entity: %s", err)
            return

        # process image data
        await self.async_process_image(image.content)

    def process_image(self, image):
        """Process the image."""
        stream = io.BytesIO(image)
        img = Image.open(stream)
        img.save(self.filepath, "png")

        with subprocess.Popen(
            self._command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=False,  # Required for posix_spawn
        ) as ocr:
            out = ocr.communicate()
            if out[0] != b"":
                self._state = out[0].strip().decode("utf-8")
            else:
                self._state = None
                _LOGGER.debug(
                    "Unable to detect value: %s", out[1].strip().decode("utf-8")
                )
            self.data_coordinator.ocr_state = self._state
            self.data_coordinator.new_image = True
            _LOGGER.debug("New image")
