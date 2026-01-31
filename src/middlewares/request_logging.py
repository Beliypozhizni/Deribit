import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()

        method = request.method
        path = request.url.path
        client = request.client.host if request.client else "-"

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "Unhandled error",
                extra={
                    "method": method,
                    "path": path,
                    "client": client,
                    "duration_ms": round(duration_ms, 2),
                },
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s -> %s (%.2f ms) client=%s",
            method,
            path,
            response.status_code,
            duration_ms,
            client,
        )
        return response
