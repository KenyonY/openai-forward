__version__ = "0.8.0"

from dotenv import load_dotenv
from yaml import load


def yaml_load(filepath):

    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader
    with open(filepath, mode='r', encoding="utf-8") as stream:
        #     stream = stream.read()
        content = load(stream, Loader=Loader)
    return content


# yaml_load()
load_dotenv('.env', override=False)
