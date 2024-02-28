"""Adds config flow for ss integration."""
import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.helpers.entity_registry import EntityRegistry, EntityRegistryItems

# from homeassistant.helpers.selector import SelectSelectorMode
from .const import DOMAIN

# _LOGGER = logging.getLogger(__name__)

# DATA_SCHEMA = vol.Schema({vol.Required(CONF_ENTITY_ID): str, vol.Required(CONF_NAME): str})


async def validate_input(hass: core.HomeAssistant, entity_id, name):
    """Validate the user input allows us to connect."""

    # Pre-validation for missing mandatory fields
    if not entity_id:
        raise MissingentityidValue("The 'entity_id' field is required.")
    if not name:
        raise MissingNameValue("The 'name' field is required.")

    for entry in hass.config_entries.async_entries(DOMAIN):
        if any(
            [
                entry.data[CONF_ENTITY_ID] == entity_id,
                entry.data[CONF_NAME] == name,
            ]
        ):
            raise AlreadyConfigured("An entry with the given details already exists.")

    # Additional validations (if any) go here...


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SS integration."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    cameras = []

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                entity_id = user_input[CONF_ENTITY_ID]
                name = user_input[CONF_NAME]
                await validate_input(self.hass, entity_id, name)

                unique_id = f"{DOMAIN}-{name}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=unique_id,
                    data={
                        CONF_ENTITY_ID: entity_id,
                        CONF_NAME: name,
                    },
                )

            except AlreadyConfigured:
                return self.async_abort(reason="already_configured")
            except MissingentityidValue:
                errors["base"] = "missing_entity_id"
            except MissingNameValue:
                errors["base"] = "missing_name"

        entity_reg: EntityRegistry = er.async_get(self.hass)
        Items: EntityRegistryItems = entity_reg.entities
        for item in Items.values():
            if item.domain == "camera" and item.disabled is False:
                self.cameras.append(item.entity_id)

        data = {
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_ENTITY_ID, default=False): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=self.cameras, mode=selector.SelectSelectorMode.DROPDOWN
                ),
            ),
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data),
            errors=errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Flowhandler."""

    cameras = []

    async def async_step_init(self, user_input=None):
        """Show form."""
        entity_reg: EntityRegistry = er.async_get(self.hass)
        Items: EntityRegistryItems = entity_reg.entities
        for item in Items.values():
            if item.domain == "camera" and item.disabled is False:
                self.cameras.append(item.entity_id)

        data_schema = {
            vol.Required(CONF_NAME): str,
            vol.Required(CONF_ENTITY_ID, default=False): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=self.cameras, mode=selector.SelectSelectorMode.DROPDOWN
                ),
            ),
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(data_schema))


@callback
def async_get_options_flow(config_entry):
    """Optionflow callback."""
    return OptionsFlowHandler(config_entry)


class MissingentityidValue(exceptions.HomeAssistantError):
    """Error to indicate entity_id is missing."""


class MissingNameValue(exceptions.HomeAssistantError):
    """Error to indicate entity_id is missing."""


class AlreadyConfigured(exceptions.HomeAssistantError):
    """Error to indicate entity_id is missing."""
