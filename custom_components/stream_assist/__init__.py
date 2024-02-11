import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceResponse, SupportsResponse
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.typing import ConfigType, ServiceCallType

from .core import DOMAIN, get_stream_source, assist_run, stream_run
from .core.stream import Stream

_LOGGER = logging.getLogger(__name__)

PLATFORMS = (Platform.SENSOR, Platform.SWITCH)


async def async_setup(hass: HomeAssistant, config: ConfigType):
    async def run(call: ServiceCallType) -> ServiceResponse:
        stt_stream = Stream()

        try:
            coro = stream_run(hass, call.data, stt_stream=stt_stream)
            hass.async_create_task(coro)

            return await assist_run(
                hass, call.data, context=call.context, stt_stream=stt_stream
            )
        except Exception as e:
            _LOGGER.error("stream_assist.run", exc_info=e)
            return {"error": {"type": str(type(e)), "message": str(e)}}
        finally:
            stt_stream.close()

    hass.services.async_register(
        DOMAIN, "run", run, supports_response=SupportsResponse.OPTIONAL
    )

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    if config_entry.data:
        hass.config_entries.async_update_entry(
            config_entry, data={}, options=config_entry.data
        )

    if not config_entry.update_listeners:
        config_entry.add_update_listener(async_update_options)

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    return True


async def async_remove_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    pass
