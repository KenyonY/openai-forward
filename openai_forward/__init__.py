__version__ = "0.1.0"

from dotenv import load_dotenv
from .config import setting_log

load_dotenv()
setting_log(log_name="openai_forward.log")
