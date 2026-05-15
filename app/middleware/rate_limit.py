from __future__ import annotations

import logging
import time

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings

logger = logging.getLogger(__name__)

EXEMPT_PATHS = {"/v1/health", "/docs", "/redoc", "/openapi.json"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        if not hasattr(request.app.state, "redis") or request.app.state.redis is None:
            return await call_next(request)

        redis = request.app.state.redis
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}"
        threshold = settings.rate_limit_requests_per_minute

        try:
            now = int(time.time())
            window = 60
            pipeline = redis.pipeline()
            pipeline.zadd(key, {str(now + i): now + i for i in range(1)})
            pipeline.zremrangebyscore(key, 0, now - window)
            pipeline.zcard(key)
            pipeline.expire(key, window)
            results = await pipeline.execute()
            count = results[2] if results else 0

            if count and int(count) > threshold:
                return JSONResponse(
                    {
                        "error": {
                            "code": "rate_limit_exceeded",
                            "message": f"Rate limit exceeded: {threshold} requests per minute",
                        }
                    },
                    status_code=429,
                    headers={"Retry-After": "60"},
                )
        except Exception:
            logger.exception("Rate limit check failed, allowing request")
            return await call_next(request)

        response = await call_next(request)
        return response
