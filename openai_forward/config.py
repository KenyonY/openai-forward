import logging
import os
import sys
import time

from loguru import logger
from rich import print
from rich.panel import Panel
from rich.table import Table


def print_startup_info(base_url, route_prefix, api_key, no_auth_mode, log_chat):
    try:
        from dotenv import load_dotenv

        load_dotenv(".env")
    except Exception:
        ...
    route_prefix = route_prefix or "/"
    api_key_info = True if len(api_key) else False
    table = Table(title="", box=None, width=100)
    table.add_column("base-url", justify="left", style="#df412f")
    table.add_column("route-prefix", justify="center", style="green")
    table.add_column("api-key-polling-pool", justify="center", style="green")
    table.add_column(
        "no-auth-mode", justify="center", style="red" if no_auth_mode else "green"
    )
    table.add_column("Log-chat", justify="center", style="green")
    table.add_row(
        base_url,
        route_prefix,
        str(api_key_info),
        str(no_auth_mode),
        str(log_chat),
    )
    print(Panel(table, title="🤗 openai-forward is ready to serve! ", expand=False))


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


def setting_log(save_file=False, log_name="openai_forward", multi_process=True):
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
        {
            "sink": f"./Log/chat.log",
            "enqueue": multi_process,
            "rotation": "20 MB",
            "filter": lambda record: "chat" in record["extra"],
            "format": "{message}",
        },
    ]
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
