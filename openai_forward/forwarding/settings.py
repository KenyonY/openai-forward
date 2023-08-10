import os

from ..config import setting_log
from ..helper import env2list, format_route_prefix

ENV_VAR_SEP = ","
OPENAI_BASE_URL = env2list("OPENAI_BASE_URL", sep=ENV_VAR_SEP)
OPENAI_ROUTE_PREFIX = [
    format_route_prefix(i) for i in env2list("OPENAI_ROUTE_PREFIX", sep=ENV_VAR_SEP)
]
if not OPENAI_ROUTE_PREFIX:
    OPENAI_ROUTE_PREFIX = ['/']

EXTRA_BASE_URL = env2list("EXTRA_BASE_URL", sep=ENV_VAR_SEP)
EXTRA_ROUTE_PREFIX = [
    format_route_prefix(i) for i in env2list("EXTRA_ROUTE_PREFIX", sep=ENV_VAR_SEP)
]

LOG_CHAT = os.environ.get("LOG_CHAT", "False").strip().lower() == "true"
if LOG_CHAT:
    setting_log(save_file=False)

IP_WHITELIST = env2list("IP_WHITELIST", sep=ENV_VAR_SEP)
IP_BLACKLIST = env2list("IP_BLACKLIST", sep=ENV_VAR_SEP)

OPENAI_API_KEY = env2list("OPENAI_API_KEY", sep=ENV_VAR_SEP)
FWD_KEY = env2list("FORWARD_KEY", sep=ENV_VAR_SEP)

PROXY = os.environ.get("PROXY", "").strip()
PROXY = PROXY if PROXY else None
