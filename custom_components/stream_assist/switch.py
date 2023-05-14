from __future__ import annotations

import logging
from datetime import timedelta
from typing import AsyncIterable, Callable

from homeassistant.components import assist_pipeline, stt
from homeassistant.components import media_player
from homeassistant.components.assist_pipeline import (
    PipelineInput,
    PipelineStage,
    PipelineRun,
    PipelineEvent,
    PipelineEventType,
    Pipeline,
)
from homeassistant.components.assist_pipeline.vad import VoiceCommandSegmenter
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_STANDBY, STATE_IDLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import DOMAIN, init_entity, get_stream_source
from .core.stream import Stream

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([StreamAssistSwitch(config_entry)])


class StreamAssistSwitch(SwitchEntity, Stream):
    _conversation_id: str = None
    vad: VoiceCommandSegmenter = None

    _attr_is_on = False
    _attr_should_poll = False
    _attr_context_recent_time = timedelta(seconds=30)

    def __init__(self, config_entry: ConfigEntry):
        self.options = config_entry.options
        self.uid = init_entity(self, "mic", config_entry)

    async def async_turn_on(self) -> None:
        if self._attr_is_on:
            return

        # 1. Check if STT entity exists
        url = self.options.get("mic_stream_url")
        if not url:
            entity_id = self.options.get("mic_entity_id")
            url = await get_stream_source(self.hass, entity_id)

        if not url:
            _LOGGER.error("Can't get stream url")
            return

        # 2. Check if stream OK
        ok = await self.hass.loop.run_in_executor(None, self.open, url)
        if not ok:
            return

        # 3. Change state
        self._attr_is_on = True
        self.async_write_ha_state()

        # 4. Run processing in separate stream
        self.hass.loop.run_in_executor(None, self.run)

        self.hass.async_create_background_task(
            self.async_process_audio_stream(), DOMAIN + "_process_audio_stream"
        )

    async def async_turn_off(self) -> None:
        if not self._attr_is_on:
            return

        self.close()

    def close(self):
        # override base close function
        if self._attr_is_on:
            self._attr_is_on = False
            self.async_write_ha_state()

        super().close()

    async def audio_stream(self, on_finish: Callable = None) -> AsyncIterable[bytes]:
        # init VAD first time
        if not self.vad:
            self.vad = VoiceCommandSegmenter()

            for k, v in self.options.items():
                if k == "vad_mode":
                    self.vad.vad_mode = v
                elif k.startswith("vad_"):  # speech_seconds, silence_seconds, etc.
                    setattr(self.vad, k[4:], v)

        in_command = None
        async_dispatcher_send(self.hass, self.uid + "-vad", STATE_STANDBY)

        while chunk := await self.audio_queue.get():
            if not self.vad.process(chunk):
                break  # Voice command is finished

            if in_command != self.vad.in_command:
                in_command = self.vad.in_command
                async_dispatcher_send(
                    self.hass, self.uid + "-vad", "voice" if in_command else "silence"
                )

            yield chunk

        async_dispatcher_send(self.hass, self.uid + "-vad", STATE_IDLE)

        on_finish()

    async def async_process_audio_stream(self):
        pipeline_end_stage = None

        # MIC => VAD => STT => NLP => TTS => SND
        end_stage = self.options.get("pipeline_end_stage")
        if end_stage != "vad":
            pipeline_id = self.options.get("pipeline_id")
            if pipeline := assist_pipeline.async_get_pipeline(self.hass, pipeline_id):
                # reduce end_stage in case of problems
                if not pipeline.stt_engine:
                    end_stage = "vad"
                elif not pipeline.tts_engine and end_stage in ("tts", "snd"):
                    end_stage = "nlp"
                elif not self.options.get("snd_entity_id") and end_stage == "snd":
                    end_stage = "tts"

                if end_stage in ("tts", "snd"):
                    pipeline_end_stage = PipelineStage.TTS
                elif end_stage == "nlp":
                    pipeline_end_stage = PipelineStage.INTENT
                elif end_stage == "stt":
                    pipeline_end_stage = PipelineStage.STT

        if pipeline_end_stage:
            await self.run_pipeline(pipeline, pipeline_end_stage)
        else:
            # just react on VAD changes
            async for _ in self.audio_stream(self.close):
                pass

    async def run_pipeline(self, pipeline: Pipeline, end_stage: PipelineStage):
        pipeline_input = PipelineInput(
            conversation_id=self._conversation_id,
            stt_metadata=stt.SpeechMetadata(
                language=pipeline.stt_language,
                format=stt.AudioFormats.WAV,
                codec=stt.AudioCodecs.PCM,
                bit_rate=stt.AudioBitRates.BITRATE_16,
                sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                channel=stt.AudioChannels.CHANNEL_MONO,
            ),
            stt_stream=self.audio_stream(self._stt_processing),
            run=PipelineRun(
                self.hass,
                context=self._context,
                pipeline=pipeline,
                start_stage=PipelineStage.STT,
                end_stage=end_stage,
                event_callback=self._event_callback,
            ),
        )

        if end_stage == PipelineStage.TTS:
            await pipeline_input.validate()
        elif end_stage == PipelineStage.INTENT:
            await pipeline_input.run.prepare_speech_to_text(pipeline_input.stt_metadata)
            await pipeline_input.run.prepare_recognize_intent()
        else:
            await pipeline_input.run.prepare_speech_to_text(pipeline_input.stt_metadata)

        await pipeline_input.execute()

    def _stt_processing(self):
        async_dispatcher_send(self.hass, self.uid + "-stt", "processing")
        self.close()

    def _event_callback(self, event: PipelineEvent):
        if not event.data:
            return

        _LOGGER.debug(f"pipeline event: {event}")

        if event.type == PipelineEventType.STT_START:
            async_dispatcher_send(self.hass, self.uid + "stt", STATE_STANDBY)

        elif event.type == PipelineEventType.STT_END:
            async_dispatcher_send(
                self.hass,
                self.uid + "-stt",
                "success",
                event.data["stt_output"],
            )

        elif event.type == PipelineEventType.INTENT_START:
            async_dispatcher_send(self.hass, self.uid + "-nlp", "processing")

        elif event.type == PipelineEventType.INTENT_END:
            self._conversation_id = event.data["intent_output"]["conversation_id"]

            response_type = event.data["intent_output"]["response"]["response_type"]
            if response_type == "error":
                response_type = event.data["intent_output"]["response"]["data"]["code"]

            async_dispatcher_send(
                self.hass,
                self.uid + "-nlp",
                response_type,
                event.data["intent_output"]["response"],
            )

        elif event.type == PipelineEventType.TTS_START:
            async_dispatcher_send(self.hass, self.uid + "-tts", "processing")

        elif event.type == PipelineEventType.TTS_END:
            async_dispatcher_send(
                self.hass, self.uid + "-tts", "success", event.data["tts_output"]
            )

            if entity_id := self.options.get("snd_entity_id"):
                data = {
                    "media_content_id": media_player.async_process_play_media_url(
                        self.hass, event.data["tts_output"]["url"]
                    ),
                    "media_content_type": event.data["tts_output"]["mime_type"],
                    "entity_id": entity_id,
                }
                coro = self.hass.services.async_call("media_player", "play_media", data)
                self.hass.async_create_background_task(coro, DOMAIN + "_play_media")

        elif event.type == PipelineEventType.ERROR:
            code: str = event.data["code"]
            if code.startswith(("stt", "tts")):
                async_dispatcher_send(
                    self.hass,
                    self.uid + "-" + code[:3],
                    code[4:].replace("-", "_"),
                    {"message": event.data["message"]},
                )
            elif code.startswith("intent"):
                async_dispatcher_send(
                    self.hass,
                    self.uid + "-nlp",
                    code[7:].replace("-", "_"),
                    {"message": event.data["message"]},
                )
