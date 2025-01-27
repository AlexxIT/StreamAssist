from __future__ import annotations
import asyncio
import logging
import io
from homeassistant.components.assist_pipeline.pipeline import (
    PipelineEvent,
    PipelineEventType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from mutagen.mp3 import MP3
from homeassistant.helpers.network import get_url
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import STATE_IDLE
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from .core import init_entity
from .core import DOMAIN
_LOGGER = logging.getLogger(__name__)

class SimpleState(SensorEntity):
    _attr_native_value = STATE_IDLE

    @property
    def streamassist_entity_name(self):
        """Return the entity name."""
        return "simple_state"

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the SimpleState sensor."""
        self.hass = hass
        self.config_entry = config_entry
        self._attr_native_value = STATE_IDLE
        self.schedule_update_ha_state()
        self.tts_duration = 0
        init_entity(self, "simple_state", config_entry)


    async def async_added_to_hass(self) -> None:
        """Subscribe to pipeline events."""
        self.remove_dispatcher = async_dispatcher_connect(
            self.hass, "simple_state_pipeline_event", self.on_pipeline_event
        )
        self.async_on_remove(self.remove_dispatcher)

    def on_pipeline_event(self, event: PipelineEvent):
        """Handle a pipeline event."""

        def getSimpleState(t: PipelineEventType) -> str:
            match t:
                case PipelineEventType.ERROR:
                    return "error"
                case PipelineEventType.WAKE_WORD_END:
                    _LOGGER.debug("PipelineEventType.WAKE_WORD_END TRIGGERED.")
                    return "detected"
                case PipelineEventType.STT_START:
                    self.hass.loop.call_soon_threadsafe(self._handle_listening_state)
                    return None
                case PipelineEventType.INTENT_START:
                    return "processing"
                case PipelineEventType.TTS_END:
                    tts_url = event.data["tts_output"]["url"]
                    self.hass.loop.call_soon_threadsafe(
                        self._handle_tts_end, tts_url
                    )
                    return "responding"
                case _:
                    return None

        state = getSimpleState(event.type)
        if state is not None:
            self._update_state(state)

    def _update_state(self, state: str):
        """Update the state safely from the event loop."""
        self._attr_native_value = state
        self.schedule_update_ha_state()

    def _handle_listening_state(self):
        """Handle the delayed update for the 'listening' state."""
        async def handle():
            try:
                await asyncio.sleep(0.5)
                self._update_state("listening")
            except Exception as e:
                _LOGGER.error(f"Error in _handle_listening_state: {e}")

        self.hass.loop.create_task(handle())

    async def get_tts_duration(self, hass: HomeAssistant, tts_url: str) -> float:
        try:
            if tts_url.startswith('/'):
                base_url = get_url(hass)
                full_url = f"{base_url}{tts_url}"
            else:
                full_url = tts_url

            session = async_get_clientsession(hass)
            async with session.get(full_url) as response:
                if response.status != 200:
                    _LOGGER.error(f"Failed to fetch TTS audio: HTTP {response.status}")
                    return 0

                content = await response.read()

            audio = MP3(io.BytesIO(content))
            return audio.info.length
        except Exception as e:
            _LOGGER.error(f"Error getting TTS duration: {e}")
            return 0

    def _handle_tts_end(self, tts_url: str):
        """Handle the end of TTS and store its duration."""

        async def handle():
            try:
                duration = await self.get_tts_duration(self.hass, tts_url)
                self.tts_duration = duration
                _LOGGER.debug(f"Stored TTS duration: {duration} seconds")

                await asyncio.sleep(duration - 0.5)
                self._update_state("finished")
            except Exception as e:
                _LOGGER.error(f"Error in _handle_tts_end: {e}")

        self.hass.loop.create_task(handle())
