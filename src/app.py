import asyncio
import logging
from logging.config import dictConfig

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from src import middlewares, settings, steam_api

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                ),
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
templates = Jinja2Templates(directory=settings.PROJECT_DIR / "src/templates")


async def index(request: Request) -> Response:
    if request.session.get("steam_id") is not None:
        return RedirectResponse(request.url_for("playground"))
    return templates.TemplateResponse(request, "pages/login.html")


async def logout(request: Request) -> Response:
    request.session.pop("steam_id", None)
    return RedirectResponse(request.url_for("index"))


async def playground(request: Request) -> Response:
    if request.session.get("steam_id") is None:
        return RedirectResponse(request.url_for("index"))

    games = await steam_api.get_owned_games(
        steam_id=request.session["steam_id"]
    )

    # Sort games from most played to least played
    games = sorted(games, key=lambda g: g.playtime, reverse=True)
    games = games[:50]  # Use no more then 50 games

    return templates.TemplateResponse(
        request=request,
        name="pages/app.html",
        context={
            "games_count": len(games),
            "games": games,
        },
    )


async def generate_context(request: Request) -> Response:
    if request.session["steam_id"] is None:
        return RedirectResponse(request.url_for("index"))

    games = await steam_api.get_owned_games(
        steam_id=request.session["steam_id"]
    )

    # Sort games from most played to least played
    games = sorted(games, key=lambda g: g.playtime, reverse=True)
    games = games[:50]  # Use no more then 50 games

    details = await asyncio.gather(
        *(
            asyncio.create_task(steam_api.get_game_details(game.appid))
            for game in games
        )
    )

    return templates.TemplateResponse(
        request=request,
        name="components/context.html",
        context={
            "games": [
                {"game": game, "game_details": game_details}
                for game, game_details in zip(games, details, strict=True)
                if details is not None
            ],
        },
    )


async def trigger_steam_login(request: Request) -> Response:
    callback_url = request.url_for("steam-login:callback")
    steam_login_url = steam_api.generate_login_url(str(callback_url))
    return RedirectResponse(steam_login_url)


async def steam_login_callback(request: Request) -> Response:
    try:
        steam_id = await steam_api.process_postlogin_params(
            params=request.query_params,
        )
    except steam_api.LoginFailedError as err:
        logger.warning(
            "Failed to finish Steam Login flow due to error: %s", err
        )
        return RedirectResponse(request.url_for("index"))

    logger.info("Steam ID: %s", steam_id)
    request.session["steam_id"] = steam_id
    return RedirectResponse(request.url_for("playground"))


app = Starlette(
    debug=settings.DEBUG,
    routes=[
        # Static files
        Mount(
            path="/static",
            app=StaticFiles(directory=settings.PROJECT_DIR / "src/static"),
            name="static",
        ),
        # Actual routes
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
            path="/playground",
            endpoint=playground,
            methods=["get"],
            name="playground",
        ),
        Route(
            path="/generate-context",
            endpoint=generate_context,
            methods=["post"],
            name="generate-context",
        ),
        Route(
            path="/",
            endpoint=index,
            methods=["get"],
            name="index",
        ),
        Route(
            "/logout",
            endpoint=logout,
            methods=["get"],
            name="logout",
        ),
    ],
    middleware=[
        Middleware(SessionMiddleware, secret_key=settings.SECRET_KEY),
        Middleware(middlewares.StaticHttpsRedirect),
    ],
)


# API for getting details about certain game:
# http://store.steampowered.com/api/appdetails?appids=<appid>&filters=<valuesToReturn>
# More at:
# https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI#appdetails
