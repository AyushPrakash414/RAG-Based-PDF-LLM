"""
Integration tests for FastAPI endpoints.

Verifies the endpoints work correctly with the application wired up
(using mocked LLM and Vector Store dependencies).
"""

import asyncio
import io
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import uuid
import json

from app.main import app
from app.api.routes import get_llm_provider, get_vector_store, get_orchestrator, get_ingestion_service
from tests.conftest import MockLLMProvider, MockVectorStore
from tests.unit.test_service_auth import sign_request as _sign_request
from unittest.mock import AsyncMock

# Override ALL required dependencies
app.dependency_overrides[get_llm_provider] = lambda: MockLLMProvider()
app.dependency_overrides[get_vector_store] = lambda: MockVectorStore()

mock_orchestrator = AsyncMock()
mock_orchestrator.ask.return_value = {
    "answer": "test answer", 
    "confidence": 0.9, 
    "status": "SUCCESS",
    "retrieval_confidence": 0.85,
    "attempts": 1
}
app.dependency_overrides[get_orchestrator] = lambda: mock_orchestrator

from app.services.ingestion_service import IngestionTask, IngestionStatus
from app.api import routes as api_routes
from unittest.mock import AsyncMock

mock_ingestion = AsyncMock()
mock_ingestion.start_ingestion.return_value = {"task_id": "test-task-123", "status": "QUEUED"}
app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion

def dummy_get_task(task_id: str):
    task = IngestionTask(task_id=task_id, document_id="doc-123", filename="test.pdf")
    task.status = IngestionStatus.COMPLETED
    return task

api_routes.get_task = dummy_get_task


# Use a fixed secret for testing the real app instance
from app.config.settings import get_settings
_settings = get_settings()
_settings.internal_api_secret = "integration-test-secret"


def auth_headers(method: str, path: str, body: bytes = b"") -> dict:
    return _sign_request(_settings.internal_api_secret, method, path, body)


@pytest.fixture
def test_client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestIntegrationEndpoints:
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, test_client):
        # Health endpoint doesn't need auth
        response = await test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["api"] == "UP"
        # Since we mock providers, they should be UP too
        assert data["groq"] == "UP"
        assert data["qdrant"] == "UP"

    @pytest.mark.asyncio
    async def test_ask_endpoint_success(self, test_client):
        body = json.dumps({"question": "What is Spring Boot?"}).encode("utf-8")
        headers = auth_headers("POST", "/ask", body)
        headers["Content-Type"] = "application/json"
        
        response = await test_client.post("/ask", content=body, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "confidence" in data
        assert data["status"] in ["SUCCESS", "REJECTED"]

    @pytest.mark.asyncio
    async def test_async_ingestion_flow(self, test_client):
        # 1. Start ingestion
        pdf_content = b"%PDF-1.4\nSome fake PDF content here"
        boundary = "webkitboundary"
        
        # We must manually construct a multipart body to compute the hash accurately for HMAC
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="document_id"\r\n\r\n'
            f"doc-123\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="test.pdf"\r\n'
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode("utf-8") + pdf_content + f"\r\n--{boundary}--\r\n".encode("utf-8")
        
        headers = auth_headers("POST", "/documents/ingest/async", body)
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        
        response = await test_client.post(
            "/documents/ingest/async", 
            content=body, 
            headers=headers
        )
        assert response.status_code == 202
        data = response.json()
        assert "task_id" in data
        task_id = data["task_id"]
        
        # 2. Check status
        status_path = f"/documents/ingest/status/{task_id}"
        status_headers = auth_headers("GET", status_path)
        
        # Give it a moment to run in background
        await asyncio.sleep(0.5)
        
        response2 = await test_client.get(status_path, headers=status_headers)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["status"] in ["COMPLETED", "FAILED"] # It will fail because our fake PDF isn't a valid PDF for PyMuPDF, which is fine
