import logging
from typing import Callable

from homeassistant.components.assist_pipeline import PipelineEvent, PipelineEventType
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import run_forever, init_entity, EVENTS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([StreamAssistSwitch(config_entry)])


class StreamAssistSwitch(SwitchEntity):
    on_close: Callable = None

    def __init__(self, config_entry: ConfigEntry):
        self._attr_is_on = False
        self._attr_should_poll = False

        self.options = config_entry.options
        self.uid = init_entity(self, "mic", config_entry)

    def event_callback(self, event: PipelineEvent):
        # Event type: wake_word-start, wake_word-end
        # Error code: wake-word-timeout, wake-provider-missing, wake-stream-failed
        code = (
            event.data["code"]
            if event.type == PipelineEventType.ERROR
            else event.type.replace("_word", "")
        )

        name, state = code.split("-", 1)

        async_dispatcher_send(self.hass, f"{self.uid}-{name}", state, event.data)

    async def async_turn_on(self) -> None:
        if self._attr_is_on:
            return

        self._attr_is_on = True
        self._async_write_ha_state()

        for event in EVENTS:
            async_dispatcher_send(self.hass, f"{self.uid}-{event}", None)

        self.on_close = run_forever(
            self.hass,
            self.options.copy(),
            context=self._context,
            event_callback=self.event_callback,
        )

    async def async_turn_off(self) -> None:
        if not self._attr_is_on:
            return

        self._attr_is_on = False
        self._async_write_ha_state()

        self.on_close()

    async def async_will_remove_from_hass(self) -> None:
        if self._attr_is_on:
            self.on_close()
