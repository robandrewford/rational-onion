from typing import Callable, Any
from slowapi import Limiter
from slowapi.util import get_remote_address

def default_key_func(request: Any) -> str:
    """Default key function for rate limiting."""
    return get_remote_address(request)

limiter = Limiter(
    key_func=default_key_func, 
    enabled=True
) 