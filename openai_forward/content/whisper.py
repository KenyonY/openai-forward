from loguru import logger


class WhisperSaver:
    def __init__(self):
        self.logger = logger.bind(whisper=True)

    def add_log(self, bytes_: bytes):
        text_content = bytes_.decode("utf-8")
        self.logger.debug(text_content)
