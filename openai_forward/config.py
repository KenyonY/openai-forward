from loguru import logger
from sparrow import relp
import sys
import logging


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setting_log(log_name, multi_process=True):
    logging.root.handlers = [InterceptHandler()]
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    logger_config = {
        "handlers": [
            {"sink": sys.stdout},
            {"sink": relp(f"../Log/{log_name}"), "enqueue": multi_process, "rotation": "100 MB"},
        ],
    }
    logger.configure(**logger_config)
