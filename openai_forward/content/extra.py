from loguru import logger


class ExtraForwardingSaver:
    def __init__(self):
        self.logger = logger.bind(extra=True)

    def add_log(self, bytes_: bytes):
        text_content = bytes_.decode("utf-8")
        self.logger.debug(text_content)
