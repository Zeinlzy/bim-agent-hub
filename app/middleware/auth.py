from __future__ import annotations

import hmac as hmac_module
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.common.keygen import hash_api_key
from app.config import settings
from app.db.connection import async_session_factory
from app.models.api_key import ApiKeyModel

logger = logging.getLogger(__name__)

EXEMPT_PATHS = {"/v1/health", "/v1/health/live", "/v1/health/ready", "/docs", "/redoc", "/openapi.json"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if not settings.auth_enabled:
            return await call_next(request)

        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": {"code": "authentication_failed", "message": "Missing or invalid Authorization header"}},
                status_code=401,
            )

        api_key = auth_header[7:]
        key_hash = hash_api_key(api_key)

        if settings.admin_api_key and hmac_module.compare_digest(api_key, settings.admin_api_key):
            request.state.api_key_name = "admin"
            return await call_next(request)

        try:
            async with async_session_factory() as db:
                result = await db.execute(
                    select(ApiKeyModel).where(
                        ApiKeyModel.key_hash == key_hash,
                        ApiKeyModel.is_active == True,
                    )
                )
                key_row = result.scalar_one_or_none()
                if not key_row:
                    return JSONResponse(
                        {"error": {"code": "authentication_failed", "message": "Invalid API key"}},
                        status_code=401,
                    )
                request.state.api_key_name = key_row.name
        except (OSError, ConnectionError):
            logger.exception("Auth DB error")
            return JSONResponse(
                {"error": {"code": "internal_error", "message": "Authentication service unavailable"}},
                status_code=503,
            )

        return await call_next(request)
