from __future__ import annotations

import traceback

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError

import logging

logger = logging.getLogger(__name__)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning("AppError: code=%s message=%s", exc.error_code, exc.message)
    return JSONResponse(
        {"error": {"code": exc.error_code, "message": exc.message}},
        status_code=exc.status_code,
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled error: %s\n%s", str(exc), traceback.format_exc())
    return JSONResponse(
        {"error": {"code": "internal_error", "message": "Internal server error"}},
        status_code=500,
    )
