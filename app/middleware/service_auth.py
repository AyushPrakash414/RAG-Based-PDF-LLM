"""
Service-to-service HMAC authentication middleware.

Re-exports from the package __init__ for cleaner imports.
"""

from app.middleware import (
    ServiceAuthMiddleware,
    generate_hmac_headers,
    _compute_signature,
)

__all__ = [
    "ServiceAuthMiddleware",
    "generate_hmac_headers",
]
