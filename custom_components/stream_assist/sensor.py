from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import STAGES, init_entity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = []

    end_stage = config_entry.options.get("pipeline_end_stage", "vad")
    for stage in STAGES:
        entities.append(StreamAssistSensor(config_entry, stage))
        if stage == end_stage or stage == "tts":
            break

    async_add_entities(entities)


class StreamAssistSensor(SensorEntity):
    _attr_native_value = STATE_IDLE

    def __init__(self, config_entry: ConfigEntry, key: str):
        init_entity(self, key, config_entry)

    async def async_added_to_hass(self) -> None:
        remove = async_dispatcher_connect(self.hass, self.unique_id, self.signal)
        self.async_on_remove(remove)

    def signal(self, value, extra: dict = None):
        self._attr_native_value = value
        self._attr_extra_state_attributes = extra
        self.async_write_ha_state()
