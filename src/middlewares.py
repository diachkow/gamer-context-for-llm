import json
from functools import cached_property
from typing import Any
from urllib.parse import unquote

from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from src import settings


class StaticHttpsRedirect(BaseHTTPMiddleware):
    """When running app in production, we must enforce `https` schema for
    static requests. Otherwise, CSS and assets are not loading.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app=app)
        self.enforce_redirect = settings.STATIC_HTTPS_REDIRECT

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request.scope["scheme"] = (
            "https"
            if self.enforce_redirect
            else request.scope.get("scheme", "http")
        )
        response = await call_next(request)
        return response


class HtmxParams:
    def __init__(self, request: Request) -> None:
        self.request = request

    def _get_header_value(self, name: str) -> str | None:
        value = self.request.headers.get(name) or None
        if value:
            if self.request.headers.get(f"{name}-URI-AutoEncoded") == "true":
                value = unquote(value)
        return value

    def __bool__(self) -> bool:
        return self._get_header_value("HX-Request") == "true"

    @cached_property
    def boosted(self) -> bool:
        return self._get_header_value("HX-Boosted") == "true"

    @cached_property
    def current_url(self) -> str | None:
        return self._get_header_value("HX-Current-URL")

    @cached_property
    def history_restore_request(self) -> bool:
        return self._get_header_value("HX-History-Restore-Request") == "true"

    @cached_property
    def prompt(self) -> str | None:
        return self._get_header_value("HX-Prompt")

    @cached_property
    def target(self) -> str | None:
        return self._get_header_value("HX-Target")

    @cached_property
    def trigger(self) -> str | None:
        return self._get_header_value("HX-Trigger")

    @cached_property
    def trigger_name(self) -> str | None:
        return self._get_header_value("HX-Trigger-Name")

    @cached_property
    def triggering_event(self) -> Any:
        value = self._get_header_value("Triggering-Event")
        if value is not None:
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                value = None
        return value


class HTMXMiddleware(BaseHTTPMiddleware):
    """Middleware to get HTMX-related headers' values and assign it directly
    to request object.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request.state.htmx = HtmxParams(request)
        return await call_next(request)
