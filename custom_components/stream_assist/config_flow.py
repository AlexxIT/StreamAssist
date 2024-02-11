import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components import assist_pipeline
from homeassistant.components.camera import CameraEntityFeature
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.config_entries import ConfigFlow, ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import entity_registry

from .core import DOMAIN


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input:
            title = user_input.pop("name")
            return self.async_create_entry(title=title, data=user_input)

        reg = entity_registry.async_get(self.hass)
        cameras = [
            k
            for k, v in reg.entities.items()
            if v.domain == "camera"
            and v.supported_features & CameraEntityFeature.STREAM
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=vol_schema(
                {
                    vol.Required("name"): str,
                    vol.Exclusive("stream_source", "url"): str,
                    vol.Exclusive("camera_entity_id", "url"): vol.In(cameras),
                },
                user_input,
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry):
        return OptionsFlowHandler(entry)


class OptionsFlowHandler(OptionsFlow):
    def __init__(self, config_entry: ConfigEntry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        reg = entity_registry.async_get(self.hass)
        cameras = [
            k
            for k, v in reg.entities.items()
            if v.domain == "camera"
            and v.supported_features & CameraEntityFeature.STREAM
        ]
        players = [
            k
            for k, v in reg.entities.items()
            if v.domain == "media_player"
            and v.supported_features & MediaPlayerEntityFeature.PLAY_MEDIA
        ]

        pipelines = {
            p.id: p.name for p in assist_pipeline.async_get_pipelines(self.hass)
        }

        defaults = self.config_entry.options.copy()

        return self.async_show_form(
            step_id="init",
            data_schema=vol_schema(
                {
                    vol.Exclusive("stream_source", "url"): str,
                    vol.Exclusive("camera_entity_id", "url"): vol.In(cameras),
                    vol.Optional("player_entity_id"): cv.multi_select(players),
                    vol.Optional("stt_start_media"): str,
                    vol.Optional("pipeline_id"): vol.In(pipelines),
                },
                defaults,
            ),
        )


def vol_schema(schema: dict, defaults: dict) -> vol.Schema:
    schema = {k: v for k, v in schema.items() if not empty(v)}

    if defaults:
        for key in schema:
            if key.schema in defaults:
                key.default = vol.default_factory(defaults[key.schema])

    return vol.Schema(schema)


def empty(v) -> bool:
    if isinstance(v, vol.In):
        return len(v.container) == 0
    if isinstance(v, cv.multi_select):
        return len(v.options) == 0
    return False
