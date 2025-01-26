from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret

PROJECT_DIR = Path(__file__).parent.parent

c = Config(PROJECT_DIR / ".env")

DEBUG = c.get("DEBUG", cast=bool, default=False)
STEAM_API_KEY = c.get("STEAM_API_KEY", cast=Secret)
LOG_LEVEL = c.get("LOG_LEVEL", cast=lambda v: str(v).upper(), default="WARNING")
