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
