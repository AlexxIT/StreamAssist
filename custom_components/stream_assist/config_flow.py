import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components import assist_pipeline
from homeassistant.components.assist_pipeline.vad import VoiceCommandSegmenter as VAD
from homeassistant.config_entries import ConfigFlow, ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import entity_registry

from .core import DOMAIN, STAGES


class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input:
            title = user_input.pop("name")
            return self.async_create_entry(title=title, data=user_input)

        reg = entity_registry.async_get(self.hass)
        cameras = [k for k, v in reg.entities.items() if v.domain == "camera"]

        return self.async_show_form(
            step_id="user",
            data_schema=schema(
                {
                    vol.Required("name"): str,
                    vol.Exclusive("mic_entity_id", "url"): vol.In(cameras),
                    vol.Exclusive("mic_stream_url", "url"): str,
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

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        reg = entity_registry.async_get(self.hass)
        cameras = [k for k, v in reg.entities.items() if v.domain == "camera"]
        players = [k for k, v in reg.entities.items() if v.domain == "media_player"]

        pipelines = {
            p.id: p.name for p in assist_pipeline.async_get_pipelines(self.hass)
        }

        stages = {p: p.upper() for p in STAGES}

        defaults = self.config_entry.options.copy()
        defaults.setdefault("vad_mode", VAD.vad_mode)
        defaults.setdefault("vad_speech_seconds", VAD.speech_seconds)
        defaults.setdefault("vad_silence_seconds", VAD.silence_seconds)
        defaults.setdefault("vad_timeout_seconds", VAD.timeout_seconds)
        defaults.setdefault("vad_reset_seconds", VAD.reset_seconds)
        defaults.setdefault("pipeline_end_stage", "vad")

        return self.async_show_form(
            step_id="init",
            data_schema=schema(
                {
                    vol.Exclusive("mic_entity_id", "url"): vol.In(cameras),
                    vol.Exclusive("mic_stream_url", "url"): str,
                    vol.Optional("vad_mode"): vol.In([0, 1, 2, 3]),
                    vol.Optional("vad_speech_seconds"): cv.positive_float,
                    vol.Optional("vad_silence_seconds"): cv.positive_float,
                    vol.Optional("vad_timeout_seconds"): cv.positive_float,
                    vol.Optional("vad_reset_seconds"): cv.positive_float,
                    vol.Optional("snd_entity_id"): cv.multi_select(players),
                    vol.Optional("pipeline_id"): vol.In(pipelines),
                    vol.Required("pipeline_end_stage"): vol.In(stages),
                },
                defaults,
            ),
        )


def schema(schema: dict, defaults: dict) -> vol.Schema:
    if defaults:
        for key in schema:
            if key.schema in defaults:
                key.default = vol.default_factory(defaults[key.schema])
    return vol.Schema(schema)
