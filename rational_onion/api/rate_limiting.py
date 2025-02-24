from typing import Callable, Any
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

def default_key_func(request: Any) -> str:
    """Default key function for rate limiting."""
    return get_remote_address(request)

def rate_limit_exceeded_handler(request: Any, exc: RateLimitExceeded) -> JSONResponse:
    """Custom handler for rate limit exceeded errors."""
    response = JSONResponse(
        status_code=429,
        content={
            "detail": {
                "error_type": "RATE_LIMIT_ERROR",
                "message": "Rate limit exceeded",
                "retry_after": str(getattr(exc, 'retry_after', None))
            }
        }
    )
    response.headers["X-RateLimit-Limit"] = str(exc.limit)
    response.headers["X-RateLimit-Remaining"] = "0"
    response.headers["X-RateLimit-Reset"] = str(getattr(exc, 'reset_at', 0))
    response.headers["Retry-After"] = str(getattr(exc, 'retry_after', 60))
    return response

limiter = Limiter(
    key_func=default_key_func,
    enabled=True,
    headers_enabled=True,
    strategy="fixed-window"
) 