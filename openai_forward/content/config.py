import functools
import logging
import os
import sys
import time
from datetime import datetime

import pytz
from loguru import logger

from ..helper import route_prefix_to_str


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 6
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setting_log(
    save_file=False,
    openai_route_prefix=None,
    log_name="openai_forward",
    multi_process=True,
    **kwargs,
):
    """
    Configures the logging settings for the application.
    """

    tz = os.environ.get("TZ", "").strip()
    if tz and hasattr(time, "tzset"):

        def get_utc_offset(timezone_str):
            timezone = pytz.timezone(timezone_str)
            offset_seconds = timezone.utcoffset(datetime.now()).total_seconds()
            offset_hours = offset_seconds // 3600
            return f"UTC{-int(offset_hours):+d}"

        try:
            os.environ["TZ"] = get_utc_offset(tz)
            time.tzset()
        except Exception:
            pass

    logging.root.handlers = [InterceptHandler()]
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    print_chat = kwargs.get('print_chat')
    config_handlers = [
        {"sink": sys.stdout, "level": "INFO" if print_chat else "DEBUG"},
    ]

    for prefix in openai_route_prefix or []:

        _prefix = route_prefix_to_str(prefix)

        config_handlers.extend(
            [
                {
                    "sink": f"./Log/{_prefix}/chat/chat.log",
                    "enqueue": multi_process,
                    "rotation": "50 MB",
                    "filter": lambda record: f"{_prefix}_chat" in record["extra"],
                    "format": "{message}",
                },
                {
                    "sink": f"./Log/{_prefix}/completion/completion.log",
                    "enqueue": multi_process,
                    "rotation": "50 MB",
                    "filter": lambda record: f"{_prefix}_completion" in record["extra"],
                    "format": "{message}",
                },
                {
                    "sink": f"./Log/{_prefix}/embedding/embedding.log",
                    "enqueue": multi_process,
                    "rotation": "100 MB",
                    "filter": lambda record: f"{_prefix}_embedding" in record["extra"],
                    "format": "{message}",
                },
                {
                    "sink": f"./Log/{_prefix}/whisper/whisper.log",
                    "enqueue": multi_process,
                    "rotation": "30 MB",
                    "filter": lambda record: f"{_prefix}_whisper" in record["extra"],
                    "format": "{message}",
                },
            ]
        )

    if save_file:
        config_handlers += [
            {
                "sink": f"./Log/{log_name}.log",
                "enqueue": multi_process,
                "rotation": "100 MB",
                "level": "INFO",
            }
        ]

    logger_config = {"handlers": config_handlers}
    logger.configure(**logger_config)
