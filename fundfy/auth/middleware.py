"""Authentication middleware."""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from fundfy.auth.jwt import decode_access_token
from fundfy.config import settings

# Routes that bypass auth
EXEMPT_PATHS = {"/health", "/ready", "/docs", "/openapi.json", "/redoc"}
EXEMPT_PREFIXES = ("/api/auth/",)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces JWT authentication on protected routes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Skip auth in test environment
        if settings.environment == "test":
            return await call_next(request)

        # Skip exempt paths
        if path in EXEMPT_PATHS:
            return await call_next(request)
        for prefix in EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Only enforce on /api/ routes
        if not path.startswith("/api/"):
            return await call_next(request)

        # Validate Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid authorization header"},
            )

        token = auth_header[7:]
        try:
            payload = decode_access_token(token)
            # Store payload in request state for route handlers
            request.state.token_payload = payload
        except ValueError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)},
            )

        return await call_next(request)
