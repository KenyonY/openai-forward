from loguru import logger
import orjson
from sparrow import relp
from typing import Union, List, Dict
import sys
import logging
import os
import time


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
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setting_log(log_name, multi_process=True):
    # TODO 修复时区配置
    if os.environ.get("TZ") == "Asia/Shanghai":
        os.environ['TZ'] = "UTC-8"
        if hasattr(time, 'tzset'):
            print(os.environ['TZ'])
            time.tzset()

    logging.root.handlers = [InterceptHandler()]
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    logger_config = {
        "handlers": [
            {"sink": sys.stdout, "level": "DEBUG"},
            {"sink": f"./Log/{log_name}.log", "enqueue": multi_process, "rotation": "100 MB", "level": "INFO"},
        ],
    }
    logger.configure(**logger_config)


def yaml_dump(data, filepath, rel_path=False, mode='w'):
    abs_path = relp(filepath, parents=1) if rel_path else filepath
    from yaml import dump

    try:
        from yaml import CDumper as Dumper
    except ImportError:
        from yaml import Dumper
    with open(abs_path, mode=mode, encoding="utf-8") as fw:
        fw.write(dump(data, Dumper=Dumper, allow_unicode=True, indent=4))


def yaml_load(filepath, rel_path=False, mode='r'):
    abs_path = relp(filepath, parents=1) if rel_path else filepath
    from yaml import load

    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader
    with open(abs_path, mode=mode, encoding="utf-8") as stream:
        #     stream = stream.read()
        content = load(stream, Loader=Loader)
    return content


def json_load(filepath: str, rel=False, mode='rb'):
    abs_path = relp(filepath, parents=1) if rel else filepath
    with open(abs_path, mode=mode) as f:
        return orjson.loads(f.read())


def json_dump(data: Union[List, Dict], filepath: str, rel=False, indent_2=False, mode='wb'):
    orjson_option = 0
    if indent_2:
        orjson_option = orjson.OPT_INDENT_2
    abs_path = relp(filepath, parents=1) if rel else filepath
    with open(abs_path, mode=mode) as f:
        f.write(orjson.dumps(data, option=orjson_option))


def str2list(s: str, sep=' '):
    if s:
        return [i.strip() for i in s.split(sep) if i.strip()]
    else:
        return []


def env2list(env_name: str, sep=" "):
    return str2list(os.environ.get(env_name, "").strip(), sep=sep)
