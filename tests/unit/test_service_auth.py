"""
Unit tests for the HMAC service-to-service authentication (Issue 4).

Tests:
1. Missing token → 401
2. Invalid token → 401
3. Expired token → 403
4. Tampered request → 401
5. Valid signature → passes
6. Health endpoint exempt
"""

import hashlib
import hmac
import json
import time

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.middleware import ServiceAuthMiddleware, _compute_signature, generate_hmac_headers

# Minimal FastAPI app for testing
from fastapi import FastAPI

TEST_SECRET = "test-secret-for-hmac-testing-only-32chars!"


def create_test_app(secret: str = TEST_SECRET) -> FastAPI:
    """Create a minimal FastAPI app with HMAC auth middleware."""
    app = FastAPI()

    if secret:
        app.add_middleware(ServiceAuthMiddleware, secret=secret)

    @app.get("/health")
    async def health():
        return {"status": "UP"}

    @app.post("/ask")
    async def ask():
        return {"answer": "test"}

    @app.post("/documents/ingest")
    async def ingest():
        return {"status": "ok"}

    @app.delete("/documents/{doc_id}")
    async def delete_doc(doc_id: str):
        return {"deleted": doc_id}

    return app


def sign_request(
    secret: str,
    method: str,
    path: str,
    body: bytes = b"",
    timestamp: str | None = None,
) -> dict[str, str]:
    """Create valid HMAC auth headers."""
    if timestamp is None:
        timestamp = str(int(time.time()))
    body_hash = hashlib.sha256(body).hexdigest()
    sig = _compute_signature(secret, timestamp, method.upper(), path, body_hash)
    return {
        "X-Service-Timestamp": timestamp,
        "X-Service-Signature": sig,
    }


class TestHMACAuth:
    """Test HMAC authentication middleware."""

    @pytest.mark.asyncio
    async def test_missing_headers_returns_401(self):
        """Request without auth headers should return 401."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/ask")
            assert response.status_code == 401
            assert "Missing authentication headers" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_missing_signature_returns_401(self):
        """Request with timestamp but no signature should return 401."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ask",
                headers={"X-Service-Timestamp": str(int(time.time()))},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_timestamp_returns_401(self):
        """Request with signature but no timestamp should return 401."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ask",
                headers={"X-Service-Signature": "fakesig"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_signature_returns_401(self):
        """Request with wrong signature should return 401."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ask",
                headers={
                    "X-Service-Timestamp": str(int(time.time())),
                    "X-Service-Signature": "0000000000000000000000000000000000000000000000000000000000000000",
                },
            )
            assert response.status_code == 401
            assert "Invalid signature" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_expired_timestamp_returns_403(self):
        """Request with timestamp older than 5 minutes should return 403."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago
            headers = sign_request(TEST_SECRET, "POST", "/ask", timestamp=old_timestamp)
            response = await client.post("/ask", headers=headers)
            assert response.status_code == 403
            assert "expired" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_invalid_timestamp_format_returns_401(self):
        """Request with non-numeric timestamp should return 401."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/ask",
                headers={
                    "X-Service-Timestamp": "not-a-number",
                    "X-Service-Signature": "fakesig",
                },
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_tampered_body_returns_401(self):
        """Signature computed with different body than sent should fail."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Sign with one body
            original_body = b'{"question": "original"}'
            headers = sign_request(TEST_SECRET, "POST", "/ask", body=original_body)
            # Send with different body
            response = await client.post(
                "/ask",
                headers=headers,
                content=b'{"question": "tampered"}',
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_valid_signature_passes(self):
        """Request with valid HMAC signature should succeed."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            body = b""
            headers = sign_request(TEST_SECRET, "POST", "/ask", body=body)
            response = await client.post("/ask", headers=headers)
            assert response.status_code == 200
            assert response.json()["answer"] == "test"

    @pytest.mark.asyncio
    async def test_valid_signature_with_body(self):
        """POST with body and valid signature should succeed."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            body = json.dumps({"question": "What is Spring Boot?"}).encode()
            headers = sign_request(TEST_SECRET, "POST", "/ask", body=body)
            headers["Content-Type"] = "application/json"
            response = await client.post("/ask", headers=headers, content=body)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_health_endpoint_exempt(self):
        """Health endpoint should not require authentication."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "UP"

    @pytest.mark.asyncio
    async def test_wrong_secret_returns_401(self):
        """Signature computed with different secret should fail."""
        app = create_test_app(secret=TEST_SECRET)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = sign_request("wrong-secret", "POST", "/ask")
            response = await client.post("/ask", headers=headers)
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_endpoint_requires_auth(self):
        """DELETE endpoints should also require authentication."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/documents/doc123")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_with_valid_auth(self):
        """DELETE with valid auth should succeed."""
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = sign_request(TEST_SECRET, "DELETE", "/documents/doc123")
            response = await client.delete("/documents/doc123", headers=headers)
            assert response.status_code == 200


class TestGenerateHmacHeaders:
    """Test the HMAC header generation utility."""

    def test_generates_required_headers(self):
        headers = generate_hmac_headers(TEST_SECRET, "POST", "/ask")
        assert "X-Service-Timestamp" in headers
        assert "X-Service-Signature" in headers

    def test_timestamp_is_recent(self):
        headers = generate_hmac_headers(TEST_SECRET, "POST", "/ask")
        ts = int(headers["X-Service-Timestamp"])
        assert abs(ts - int(time.time())) < 5

    def test_signature_is_hex(self):
        headers = generate_hmac_headers(TEST_SECRET, "POST", "/ask")
        sig = headers["X-Service-Signature"]
        assert len(sig) == 64  # SHA-256 hex digest
        int(sig, 16)  # Should be valid hex

    def test_different_bodies_produce_different_signatures(self):
        h1 = generate_hmac_headers(TEST_SECRET, "POST", "/ask", body=b"body1")
        h2 = generate_hmac_headers(TEST_SECRET, "POST", "/ask", body=b"body2")
        assert h1["X-Service-Signature"] != h2["X-Service-Signature"]

    def test_different_paths_produce_different_signatures(self):
        h1 = generate_hmac_headers(TEST_SECRET, "POST", "/ask")
        h2 = generate_hmac_headers(TEST_SECRET, "POST", "/documents/ingest")
        assert h1["X-Service-Signature"] != h2["X-Service-Signature"]
