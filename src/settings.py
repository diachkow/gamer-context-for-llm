from pathlib import Path

from starlette.config import Config
from starlette.datastructures import Secret

PROJECT_DIR = Path(__file__).parent.parent
ENV_FILE_PATH: Path = PROJECT_DIR / ".env"

c: Config
if ENV_FILE_PATH.exists():
    c = Config(PROJECT_DIR / ".env")
else:
    c = Config()

DEBUG = c.get("DEBUG", cast=bool, default=False)
STEAM_API_KEY = c.get("STEAM_API_KEY", cast=Secret)
SECRET_KEY = c.get("SECRET_KEY", cast=Secret)
LOG_LEVEL = c.get(
    "LOG_LEVEL",
    cast=lambda v: str(v).upper(),
    default="WARNING",
)
STATIC_HTTPS_REDIRECT = c.get(
    "STATIC_HTTPS_REDIRECT",
    cast=bool,
    default=False,
)
