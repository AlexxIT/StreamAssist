import logging
from asyncio import Queue

import av
from av.audio.resampler import AudioResampler
from av.container import InputContainer

_LOGGER = logging.getLogger(__name__)


class Stream:
    container: InputContainer | None
    audio_queue: Queue[bytes | None]

    def open(self, url: str):
        options = {"fflags": "nobuffer", "flags": "low_delay", "timeout": "5000000"}

        if url.startswith("rtsp"):
            options["rtsp_flags"] = "prefer_tcp"
            options["allowed_media_types"] = "audio"

        _LOGGER.debug(f"open: {url}")

        self.container = av.open(url, options=options, timeout=5)
        self.audio_queue = Queue()

    def run(self):
        _LOGGER.debug(f"run")

        # TODO: support other formats
        resampler = AudioResampler(format="s16", layout="mono", rate=16000)

        try:
            for frame in self.container.decode(audio=0):
                for new_frame in resampler.resample(frame):
                    self.audio_queue.put_nowait(new_frame.to_ndarray().tobytes())
        except Exception as e:
            if not isinstance(e, OSError) or e.errno != 10038:
                _LOGGER.error("run", exc_info=e)
        finally:
            self.close()

    def close(self):
        if not self.container:
            return

        _LOGGER.debug(f"close")

        try:
            self.container.close()
            self.container = None
        except Exception as e:
            _LOGGER.error("close", exc_info=e)
        finally:
            self.audio_queue.put_nowait(None)
