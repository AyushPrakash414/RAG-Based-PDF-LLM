"""
Service-to-service HMAC authentication middleware for FastAPI.

Validates that incoming requests are signed by an authorized service
using HMAC-SHA256 signatures with replay protection.

Signature scheme:
    signature = HMAC-SHA256(secret, timestamp + method + path + body_sha256)

Required headers:
    X-Service-Timestamp: Unix epoch seconds
    X-Service-Signature: hex-encoded HMAC signature
"""

import hashlib
import hmac
import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Maximum age of a signed request (5 minutes) — prevents replay attacks
MAX_TIMESTAMP_DRIFT_SECONDS = 300

# Paths exempt from authentication
EXEMPT_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


def _compute_signature(
    secret: str,
    timestamp: str,
    method: str,
    path: str,
    body_hash: str,
) -> str:
    """
    Compute HMAC-SHA256 signature for request verification.

    Args:
        secret: Shared secret key.
        timestamp: Unix epoch timestamp string.
        method: HTTP method (uppercase).
        path: Request path.
        body_hash: SHA-256 hex digest of the request body.

    Returns:
        Hex-encoded HMAC-SHA256 signature.
    """
    message = f"{timestamp}.{method}.{path}.{body_hash}"
    return hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class ServiceAuthMiddleware(BaseHTTPMiddleware):
    """
    HMAC-based service-to-service authentication middleware.

    Validates X-Service-Timestamp and X-Service-Signature headers
    on every request except exempt paths.
    """

    def __init__(self, app, secret: str) -> None:
        """
        Initialise the middleware.

        Args:
            app: The FastAPI application.
            secret: The shared secret for HMAC signing.
        """
        super().__init__(app)
        self._secret = secret
        if not secret:
            logger.warning(
                "INTERNAL_API_SECRET is empty — service auth middleware "
                "will REJECT all non-exempt requests!"
            )

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Validate HMAC signature before forwarding the request."""

        # Skip auth for exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Skip auth for OPTIONS (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract headers
        timestamp = request.headers.get("X-Service-Timestamp")
        signature = request.headers.get("X-Service-Signature")

        if not timestamp or not signature:
            logger.warning(
                "Missing auth headers: path=%s, has_timestamp=%s, has_signature=%s",
                request.url.path,
                bool(timestamp),
                bool(signature),
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication headers"},
            )

        # Validate timestamp freshness (replay protection)
        try:
            request_time = int(timestamp)
            current_time = int(time.time())
            drift = abs(current_time - request_time)

            if drift > MAX_TIMESTAMP_DRIFT_SECONDS:
                logger.warning(
                    "Request timestamp expired: drift=%ds, max=%ds, path=%s",
                    drift,
                    MAX_TIMESTAMP_DRIFT_SECONDS,
                    request.url.path,
                )
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Request timestamp expired"},
                )
        except (ValueError, TypeError):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid timestamp format"},
            )

        # Read body for signature computation
        body = await request.body()
        body_hash = hashlib.sha256(body).hexdigest()

        # Compute expected signature
        expected_signature = _compute_signature(
            secret=self._secret,
            timestamp=timestamp,
            method=request.method.upper(),
            path=request.url.path,
            body_hash=body_hash,
        )

        # Constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning(
                "Invalid HMAC signature: path=%s, method=%s",
                request.url.path,
                request.method,
            )
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid signature"},
            )

        logger.debug(
            "HMAC auth passed: path=%s, method=%s",
            request.url.path,
            request.method,
        )
        return await call_next(request)


def generate_hmac_headers(
    secret: str,
    method: str,
    path: str,
    body: bytes = b"",
) -> dict[str, str]:
    """
    Generate HMAC authentication headers for an outgoing request.

    Utility function for clients that need to sign requests.

    Args:
        secret: The shared secret key.
        method: HTTP method (e.g., "POST").
        path: Request path (e.g., "/ask").
        body: Request body bytes.

    Returns:
        Dict with X-Service-Timestamp and X-Service-Signature headers.
    """
    timestamp = str(int(time.time()))
    body_hash = hashlib.sha256(body).hexdigest()
    signature = _compute_signature(
        secret=secret,
        timestamp=timestamp,
        method=method.upper(),
        path=path,
        body_hash=body_hash,
    )
    return {
        "X-Service-Timestamp": timestamp,
        "X-Service-Signature": signature,
    }
