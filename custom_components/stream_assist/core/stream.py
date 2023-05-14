import logging
from asyncio import Queue

import av
from av.audio.resampler import AudioResampler
from av.container import InputContainer

_LOGGER = logging.getLogger(__name__)


class Stream:
    running: bool = False
    container: InputContainer = None
    audio_queue: Queue[bytes] = None

    def open(self, url: str) -> bool:
        if self.container:
            _LOGGER.error("can't reopen active stream")
            return False

        options = {"fflags": "nobuffer", "flags": "low_delay", "timeout": "5000000"}

        if url.startswith("rtsp"):
            options["rtsp_flags"] = "prefer_tcp"
            options["allowed_media_types"] = "audio"

        _LOGGER.debug(f"open: {url}")

        try:
            self.container = av.open(url, options=options, timeout=5)
            self.audio_queue = Queue()
            return True
        except Exception as e:
            _LOGGER.error("open", exc_info=e)
            self.container = None
            return False

    def run(self):
        _LOGGER.debug(f"run")

        # TODO: support other formats
        resampler = AudioResampler(format="s16", layout="mono", rate=16000)

        try:
            self.running = True
            while self.running:
                frame = next(self.container.decode(audio=0))
                for new_frame in resampler.resample(frame):
                    self.audio_queue.put_nowait(new_frame.to_ndarray().tobytes())
        except Exception as e:
            _LOGGER.error("run", exc_info=e)
        finally:
            self.audio_queue.put_nowait(None)
            self.container.close()
            self.container = None

    def close(self):
        _LOGGER.debug(f"close")

        self.running = False
