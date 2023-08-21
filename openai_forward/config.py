import functools
import logging
import os
import sys
import time

from loguru import logger
from rich import print
from rich.panel import Panel
from rich.table import Table


def print_startup_info(base_url, route_prefix, api_key, fwd_key, /, style, **kwargs):
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
    }
    table.add_column("", justify='left', width=10)
    table.add_column("", justify='left')
    for key, value in matrcs.items():
        table.add_row(key, value['value'], style=value.get('style', style))
    for key, value in kwargs.items():
        table.add_row(key, str(value), style=style)

    print(Panel(table, title="🤗 openai-forward is ready to serve! ", expand=False))


def print_rate_limit_info(
    strategy: str,
    global_req_rate_limit: str,
    req_rate_limit: dict,
    token_rate_limit: dict,
    **kwargs,
):
    """
    Print rate limit information.

    Args:
        strategy (str): The strategy used for rate limiting.
        global_req_rate_limit (str): The global request rate limit.
        req_rate_limit (dict): A dictionary of request rate limit.
        token_rate_limit (dict): A dictionary of token rate limit.
        **kwargs: Other limits info.

    Returns:
        None
    """
    table = Table(title="", box=None, width=50)
    table.add_column("")
    table.add_column("", justify='left')
    if strategy:
        table.add_row("strategy", strategy, style='#7CD9FF')

    table.add_row(
        "global rate limit", f"{global_req_rate_limit} (req)", style='#C5FF95'
    )
    for key, value in req_rate_limit.items():
        table.add_row(key, f"{value} (req)", style='#C5FF95')

    for key, value in token_rate_limit.items():
        if isinstance(value, float):
            value = f"{value:.4f} s/token"
        table.add_row(key, f"{value} (token)", style='#C5FF95')

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
    **kwargs,
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

    print_chat = kwargs.get('print_chat')
    config_handlers = [
        {"sink": sys.stdout, "level": "INFO" if print_chat else "DEBUG"},
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
