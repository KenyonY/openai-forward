from loguru import logger


class ExtraForwardingSaver:
    def __init__(self, route_prefix: str):
        _prefix = route_prefix.replace('/', '_')
        self.logger = logger.bind(**{f"{_prefix}_extra": True})

    def add_log(self, bytes_: bytes):
        text_content = bytes_.decode("utf-8")
        self.logger.debug(text_content)
