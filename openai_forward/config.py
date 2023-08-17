import functools
import logging
import os
import sys
import time

from loguru import logger
from rich import print
from rich.panel import Panel
from rich.table import Table


def print_startup_info(base_url, route_prefix, api_key, fwd_key, log_chat, style):
    """
    Prints the startup information of the application.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(".env")
    except Exception:
        ...
    route_prefix = route_prefix or "/"
    if not isinstance(api_key, str):
        api_key = True if len(api_key) else False
    if not isinstance(fwd_key, str):
        fwd_key = True if len(fwd_key) else False
    table = Table(title="", box=None, width=50)

    matrcs = {
        "base url": {
            'value': base_url,
        },
        "route prefix": {
            'value': route_prefix,
        },
        "api keys": {
            'value': str(api_key),
        },
        "forward keys": {
            'value': str(fwd_key),
            'style': "#62E883" if fwd_key or not api_key else "red",
        },
        "Log chat": {
            'value': str(log_chat),
        },
    }
    table.add_column("", justify='left', width=10)
    table.add_column("", justify='left')
    for key, value in matrcs.items():
        table.add_row(key, value['value'], style=value.get('style', style))

    print(Panel(table, title="🤗 openai-forward is ready to serve! ", expand=False))


def print_rate_limit_info(rate_limit: dict, strategy: str, **kwargs):
    """
    Print rate limit information.

    Args:
        rate_limit (dict): A dictionary containing route rate limit.
        strategy (str): The strategy used for rate limiting.
        **kwargs: Other limits info.

    Returns:
        None
    """
    table = Table(title="", box=None, width=50)
    table.add_column("")
    table.add_column("", justify='left')
    table.add_row("strategy", strategy, style='#7CD9FF')
    for key, value in rate_limit.items():
        table.add_row(key, str(value), style='#C5FF95')
    for key, value in kwargs.items():
        table.add_row(key, str(value), style='#C5FF95')
    print(Panel(table, title="⏱️ Rate Limit configuration", expand=False))


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
):
    """
    Configures the logging settings for the application.
    """
    # TODO 修复时区配置
    if os.environ.get("TZ") == "Asia/Shanghai":
        os.environ["TZ"] = "UTC-8"
        if hasattr(time, "tzset"):
            time.tzset()

    logging.root.handlers = [InterceptHandler()]
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    config_handlers = [
        {"sink": sys.stdout, "level": "DEBUG"},
    ]

    def filter_func(_prefix, _postfix, record):
        chat_key = f"{_prefix}{_postfix}"
        return chat_key in record["extra"]

    for prefix in openai_route_prefix or []:
        _prefix = prefix.replace('/', '_')

        config_handlers.extend(
            [
                {
                    "sink": f"./Log/chat/{_prefix}/chat.log",
                    "enqueue": multi_process,
                    "rotation": "50 MB",
                    "filter": functools.partial(filter_func, _prefix, "_chat"),
                    "format": "{message}",
                },
                {
                    "sink": f"./Log/whisper/{_prefix}/whisper.log",
                    "enqueue": multi_process,
                    "rotation": "30 MB",
                    "filter": functools.partial(filter_func, _prefix, "_whisper"),
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
