import re
from typing import Final

import httpx

from starlette import status
from starlette.applications import Starlette
from starlette.config import Config
from starlette.datastructures import QueryParams
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse, Response

env = Config(".env")

DEBUG = env.get("DEBUG", cast=bool, default=False)
STEAM_API_KEY = env.get("STEAM_API_KEY", cast=str)

STEAM_OPENID_LOGIN_URL: Final[str] = "https://steamcommunity.com/openid/login"


app = Starlette(debug=DEBUG)


class LoginFailedError(Exception):
    """Raised whenever Steam OpenID 2.0 login failed"""


def steam_login_redirect(app_redirect_url: str) -> str:
    steam_login_query_params = QueryParams(
        {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": app_redirect_url,
            "openid.realm": app_redirect_url,
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }
    )
    return f"{STEAM_OPENID_LOGIN_URL}?{steam_login_query_params}"


async def process_after_login_params(params: QueryParams) -> str:
    validation_params: dict[str, str] = {
        key: val
        for key, val in params.items()
        if key in ["openid.assoc_handle", "openid.signed", "openid.sig", "openid.ns"]
    }
    signed_params: list[str] = params["openid.signed"].split(",")

    for item in signed_params:
        key = f"openid.{item}"
        if key not in validation_params:
            validation_params[key] = params[key]

    validation_params["openid.mode"] = "check_authentication"

    async with httpx.AsyncClient() as client:
        r = await client.get(url=STEAM_OPENID_LOGIN_URL, params=validation_params)

        if r.status_code != status.HTTP_200_OK:
            raise LoginFailedError(
                f"Received non-200 status code (code: {r.status_code},"
                f" content: {r.content!r})"
            )

        if "is_valid:true" in r.text:
            matched_steam_id = re.search(
                r"https://steamcommunity.com/openid/id/(\d+)",
                params["openid.claimed_id"],
            )

            if not matched_steam_id:
                raise LoginFailedError(
                    f"Claimed ID is not found in validation response: {r.text}"
                )

            return matched_steam_id.group(1)
        else:
            raise LoginFailedError(
                f"Validation response does not contain 'is_valid:true' at the end: {r.text}"
            )


@app.route(path="/", methods=["get"], name="index")
async def homepage(request: Request) -> Response:
    after_login_redirect: str = request.url_for("login_redirect_url")
    return RedirectResponse(
        url=steam_login_redirect(
            app_redirect_url=after_login_redirect,
        ),
    )


@app.route(path="/steam-login", methods=["get"], name="login_redirect_url")
async def login_redirect_url(request: Request) -> Response:
    steam_id = await process_after_login_params(request.query_params)
    return JSONResponse({"steamid": steam_id})


@app.route(path="/owned-games", methods=["get"], name="owned_games")
async def owned_games(request: Request) -> Response:
    if "steamid" not in request.query_params:
        return JSONResponse(
            {"steamid": "Query parameter missing"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"

    async with httpx.AsyncClient() as client:
        r = await client.get(
            url=url,
            params={
                "steamid": request.query_params["steamid"],
                "key": STEAM_API_KEY,
                "format": "json",
            },
        )
        r.raise_for_status()

        return JSONResponse(content=r.json())


# API for getting details about certain game:
# http://store.steampowered.com/api/appdetails?appids=<appid>&filters=<valuesToReturn>
# More at:
# https://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI#appdetails
