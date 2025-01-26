import logging
from logging.config import dictConfig


from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response
from starlette.routing import Mount, Route

from src import settings, steam_api

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "app": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
        },
    }
)

logger = logging.getLogger("app")


async def trigger_steam_login(request: Request) -> Response:
    callback_url = request.url_for("steam-login:callback")
    steam_login_url = steam_api.generate_login_url(callback_url)
    return RedirectResponse(steam_login_url)


async def steam_login_callback(request: Request) -> Response:
    try:
        steam_id = await steam_api.process_postlogin_params(
            params=request.query_params,
        )
    except steam_api.LoginFailedError as err:
        logger.warning("Failed to finish Steam Login flow due to error: %s", err)
        return JSONResponse({"error": str(err)})

    logger.info("Steam ID: %s", steam_id)
    return JSONResponse({"steamid": steam_id})


async def owned_games(request: Request) -> Response:
    if "steamid" not in request.query_params:
        return JSONResponse({"steamid": "Missing query parameter"})

    try:
        owned_games = await steam_api.get_owned_games(request.query_params["steamid"])
    except steam_api.SteamAPIRequestFailed as err:
        logger.warning("Failed to fetch user owned games due to error: %s", err)
        return JSONResponse({"error": "Failed to fetch user owned games"})

    return JSONResponse(owned_games)


app = Starlette(
    debug=settings.DEBUG,
    routes=[
        Mount(
            path="/steam-login",
            routes=[
                Route(
                    path="/trigger",
                    endpoint=trigger_steam_login,
                    name="trigger",
                    methods=["get"],
                ),
                Route(
                    path="/callback",
                    endpoint=steam_login_callback,
                    name="callback",
                    methods=["get"],
                ),
            ],
            name="steam-login",
        ),
        Route(
            path="/owned-games",
            endpoint=owned_games,
            methods=["get"],
            name="owned-games",
        ),
    ],
)


# API for getting details about certain game:
# http://store.steampowered.com/api/appdetails?appids=<appid>&filters=<valuesToReturn>
# More at:
# https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI#appdetails
