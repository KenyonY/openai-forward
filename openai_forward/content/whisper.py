from loguru import logger


class WhisperSaver:
    def __init__(self, route_prefix: str):
        _prefix = route_prefix.replace('/', '_')
        self.logger = logger.bind(**{f"{_prefix}_whisper": True})

    def add_log(self, bytes_: bytes):
        text_content = bytes_.decode("utf-8")
        self.logger.debug(text_content)
