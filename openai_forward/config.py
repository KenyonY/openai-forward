import functools
import logging
import os
import sys
import time

from loguru import logger
from rich import print
from rich.panel import Panel
from rich.table import Table


def print_startup_info(base_url, route_prefix, api_key, fwd_key, log_chat):
    """
    Prints the startup information of the application.
    """
    try:
        from dotenv import load_dotenv

        load_dotenv(".env")
    except Exception:
        ...
    route_prefix = route_prefix or "/"
    if isinstance(api_key, str):
        api_key = api_key
    else:
        api_key = str(True if len(api_key) else False)
    if isinstance(fwd_key, str):
        fwd_key = fwd_key
    else:
        fwd_key = True if len(fwd_key) else False
    table = Table(title="", box=None, width=50)

    matrcs = {
        "base url": {'value': base_url, 'style': "#df412f"},
        "route prefix": {'value': route_prefix, 'style': "green"},
        "api keys": {'value': api_key, 'style': "green"},
        "forward keys": {'value': str(fwd_key), 'style': "green" if fwd_key else "red"},
        "Log chat": {'value': str(log_chat), 'style': "green"},
    }
    table.add_column("matrcs", justify='left', width=10)
    table.add_column("value", justify='left')
    for key, value in matrcs.items():
        table.add_row(key, value['value'], style=value['style'])

    print(Panel(table, title="🤗 openai-forward is ready to serve! ", expand=False))


def show_rate_limit_info(rate_limit: dict, strategy: str, **kwargs):
    """
    Print rate limit information.

    Parameters:
        rate_limit (dict): A dictionary containing rate limit information.
        strategy (str): The strategy used for rate limiting.
        **kwargs: Additional keyword arguments.

    Returns:
        None
    """
    table = Table(title="", box=None, width=50)
    table.add_column("matrics")
    table.add_column("value")
    table.add_row("strategy", strategy, style='blue')
    for key, value in rate_limit.items():
        table.add_row(key, str(value), style='green')
    for key, value in kwargs.items():
        table.add_row(key, str(value), style='green')
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
