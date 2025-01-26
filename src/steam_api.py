"""All functions related to working with Steam API."""

import re
from typing import Final, Mapping

import httpx
from starlette import status
from starlette.datastructures import QueryParams

from src import settings


class LoginFailedError(Exception):
    """Raised whenever Steam Login has failed."""


STEAM_LOGIN_URL: Final[str] = "https://steamcommunity.com/openid/login"
STEAM_ID_REGEX: Final[str] = r"https://steamcommunity.com/openid/id/(\d+)"


def generate_login_url(callback_url: str) -> str:
    """Start OpenID login flow for Steam API.

    :param callback_url: Application URL to redirect to after successful login.

    :returns: A Steam API login URL that user shall be redirected to in order
        to start login flow.
    """
    steam_login_query_params = QueryParams(
        {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": callback_url,
            "openid.realm": callback_url,
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        },
    )
    return f"{STEAM_LOGIN_URL}?{steam_login_query_params}"


async def process_postlogin_params(params: Mapping[str, str]) -> str:
    """Verify post-login parameters & fetch user Steam ID.

    :param params: A mapping of query parameters received after user has
        completed Steam OpenAI login flow. This params are later used to make
        additional verification request & fetch user Steam ID.

    :raises LoginFailedError: In case if params verification has failed or
        the flow was unable to fetch user Steam ID.

    :returns: User Steam ID.
    """
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
        r = await client.get(url=STEAM_LOGIN_URL, params=validation_params)

        if r.status_code != status.HTTP_200_OK:
            raise LoginFailedError(
                f"Received non-200 status code (code: {r.status_code},"
                f" content: {r.content!r})"
            )

        if "is_valid:true" not in r.text:
            raise LoginFailedError(
                f"Validation response does not contain 'is_valid:true' at the end: {r.text}"
            )

        matched_steam_id = re.search(STEAM_ID_REGEX, params["openid.claimed_id"])

        if not matched_steam_id:
            raise LoginFailedError(
                f"Claimed ID is not found in validation response: {r.text}"
            )

        return matched_steam_id.group(1)


class SteamAPIRequestFailed(Exception):
    """Wrapper exception class for Steam API call failures."""

    def __init__(
        self,
        original_message: str,
        original_request: httpx.Request | None = None,
        original_response: httpx.Response | None = None,
    ) -> None:
        self._message = str
        self._request = original_request
        self._response = original_response

    def __str__(self) -> str:
        return self._message

    @property
    def request(self) -> httpx.Request:
        if self._request is None:
            raise AttributeError("Request is not set")
        return self._request

    @property
    def response(self) -> httpx.Response:
        if self._response is None:
            raise AttributeError("Response is not set")
        return self._response


async def get_owned_games(steam_id: str):
    """Get the list of user-owned games.

    :param steam_id: Steam user unique identifier.

    :raises SteamAPIRequestFailed: In case if fetching games list has failed.

    :returns: Raw response data of owned games request.
    """
    url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"

    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(
                url=url,
                params={
                    "steamid": steam_id,
                    "key": str(settings.STEAM_API_KEY),
                    "format": "json",
                },
            )
            r.raise_for_status()
        except httpx.HTTPError as err:
            raise SteamAPIRequestFailed(
                original_message=str(err),
                original_request=err.request,
                original_response=getattr(err, "response", None),
            ) from err

        return r.json()
