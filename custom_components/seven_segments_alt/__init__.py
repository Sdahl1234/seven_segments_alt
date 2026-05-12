"""The seven_segments component."""

# import asyncio
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

from PIL import Image

from homeassistant.components.image import ImageEntity
from homeassistant.components.image_processing import ImageProcessingEntity
from homeassistant.config import ConfigType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

# from . import ImageProcessingSsocr
from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    SS_CAM,
    SS_DIGITS,
    SS_EXTRA_ARGUMENTS,
    SS_HEIGHT,
    SS_ROTATE,
    SS_THRESHOLD,
    SS_WIDTH,
    SS_X_POS,
    SS_Y_POS,
)

# from .image_processing import ImageProcessingSsocr

STORAGE_VERSION = 1

PLATFORMS = [
    Platform.BUTTON,
    Platform.IMAGE,
    Platform.NUMBER,
    #    Platform.SELECT,
    Platform.SENSOR,
    Platform.TEXT,
]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType):  # noqa: D103
    hass.async_create_task(
        async_load_platform(hass, Platform.IMAGE_PROCESSING, DOMAIN, {}, config)
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up the SS."""

    ei = entry.data.get(CONF_ENTITY_ID)
    name = entry.data.get(CONF_NAME)
    data_coordinator = SSDataCoordinator(hass, ei, name, entry.entry_id)
    await data_coordinator.async_init_data()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    hass.data[DOMAIN][entry.entry_id] = data_coordinator
    hass.data[DOMAIN][DATA_COORDINATOR] = data_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_entry))
    return True


async def async_update_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class SSDataCoordinator(DataUpdateCoordinator):  # noqa: D101
    # config_entry: ConfigEntry

    # cfile: io.TextIOWrapper = None
    componentname: str
    img_path: str
    processed_name: str
    new_image: bool = False
    image_entity: ImageEntity
    image_entity_2: ImageEntity
    image_entity_3: ImageEntity
    ocr_image: Image
    ocr_entity: ImageProcessingEntity
    ocr_state: str = None
    camera_entity_id: str
    jdata: None
    data_loaded: bool = False
    data_default = {
        SS_X_POS: 0,
        SS_Y_POS: 0,
        SS_HEIGHT: 0,
        SS_WIDTH: 0,
        SS_ROTATE: 0,
        SS_THRESHOLD: 0,
        SS_DIGITS: -1,
        SS_EXTRA_ARGUMENTS: "",
        SS_CAM: "",
    }

    def __init__(self, hass: HomeAssistant, ei: str, name: str, entry_id: str) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=10),  # 60 * 60),
        )
        self.camera_entity_id = ei
        self.always_update = True
        self._name = name
        self.componentname = name
        self.store: Store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")
        self.filepath = Path(self.hass.config.config_dir) / "ssocr-{}.json".format(
            self.componentname.replace(" ", "_")
        )
        pn = f"{self.componentname}_img_processed.png".replace(" ", "_")
        self.processed_name = Path(self.hass.config.config_dir) / pn
        # self.processed_name = f"{self.componentname}_img_processed.png"
        self.mandatory_extras = f"-D{self.processed_name}"
        _LOGGER.debug(self.filepath)
        _LOGGER.debug(self.processed_name)
        _LOGGER.debug(self.mandatory_extras)

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.unique_id),
            },
            manufacturer="Seven Segments",
            name=self.componentname,
        )

    @property
    def unique_id(self) -> str:
        """Return the system descriptor."""
        return f"{DOMAIN}-{self.componentname}"

    async def set_default_data(self):
        """Set default."""
        self.jdata = self.data_default
        self.jdata[SS_X_POS] = 990
        self.jdata[SS_Y_POS] = 180
        self.jdata[SS_HEIGHT] = 180
        self.jdata[SS_WIDTH] = 770
        self.jdata[SS_ROTATE] = 0
        self.jdata[SS_THRESHOLD] = 44
        self.jdata[SS_DIGITS] = 7
        self.jdata[SS_EXTRA_ARGUMENTS] = "-cdecimal"
        self.jdata[SS_CAM] = self.camera_entity_id

    async def async_init_data(self):
        """Load data from storage, migrating from legacy file if needed."""
        stored = await self.store.async_load()
        if stored is not None:
            self.jdata = stored
            self.data_loaded = True
            return

        # Migrate from the legacy plain-JSON file if it exists.
        def _read_legacy_file():
            try:
                with self.filepath.open(encoding="utf-8") as fh:
                    return json.loads(fh.read())
            except FileNotFoundError:
                return None

        legacy = await self.hass.async_add_executor_job(_read_legacy_file)
        if legacy is not None:
            _LOGGER.info(
                "Migrating seven_segments_alt data from %s to HA storage",
                self.filepath,
            )
            self.jdata = legacy
            await self.store.async_save(self.jdata)
            await self.hass.async_add_executor_job(self.filepath.unlink)
            self.data_loaded = True
            return

        # No existing data — initialise with defaults.
        await self.set_default_data()
        await self.store.async_save(self.jdata)

    async def save_data(self, append: bool):
        """Save data to HA storage."""
        try:
            await self.store.async_save(self.jdata)
        except Exception as ex:  # pylint: disable=broad-except  # noqa: BLE001
            _LOGGER.debug(f"Save data failed: {ex}")  # noqa: G004

    async def load_data(self):
        """Load data from HA storage."""
        try:
            stored = await self.store.async_load()
            if stored is not None:
                _LOGGER.debug(f"loaded: {stored}")  # noqa: G004
                self.jdata = stored
                self.data_loaded = True
        except Exception as ex:  # pylint: disable=broad-except  # noqa: BLE001
            _LOGGER.debug(f"load data failed: {ex}")  # noqa: G004

    async def _async_update_data(self):
        try:
            # await self.hass.async_add_executor_job(self.data_handler.update)
            await self.ocr_entity.async_update()
            if self.new_image:
                self.new_image = False
                self.image_entity.image_last_updated = datetime.now()
                self.image_entity_2.image_last_updated = datetime.now()
                self.image_entity_3.image_last_updated = datetime.now()
        except Exception as ex:  # pylint: disable=broad-except  # noqa: BLE001
            _LOGGER.debug(f"update failed: {ex}")  # noqa: G004
