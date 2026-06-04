"""
Load test for the FastAPI endpoints.

Simulates multiple concurrent users asking questions simultaneously.
"""

import asyncio
import time
import pytest
from httpx import AsyncClient, ASGITransport
import json

from app.main import app
from app.api.routes import get_llm_provider, get_vector_store, get_orchestrator
from tests.conftest import MockLLMProvider, MockVectorStore
from tests.unit.test_service_auth import sign_request
from unittest.mock import AsyncMock

# Override dependencies
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

from app.config.settings import get_settings
_settings = get_settings()
_settings.internal_api_secret = "load-test-secret"


async def simulate_user(client: AsyncClient, user_id: int):
    """Simulate a single user asking a question."""
    body = json.dumps({"question": f"Load test question from user {user_id}"}).encode("utf-8")
    headers = sign_request("load-test-secret", "POST", "/ask", body)
    headers["Content-Type"] = "application/json"
    
    start_time = time.perf_counter()
    response = await client.post("/ask", content=body, headers=headers)
    end_time = time.perf_counter()
    
    latency = end_time - start_time
    assert response.status_code == 200
    
    return latency


@pytest.mark.asyncio
async def test_concurrent_load():
    """Run concurrent load test against the /ask endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Simulate 100 concurrent requests
        concurrency = 100
        tasks = [simulate_user(client, i) for i in range(concurrency)]
        
        start_time = time.perf_counter()
        latencies = await asyncio.gather(*tasks)
        end_time = time.perf_counter()
        
        total_time = end_time - start_time
        avg_latency = sum(latencies) / len(latencies)
        
        # Sort latencies to find P95
        latencies.sort()
        p95_latency = latencies[int(len(latencies) * 0.95)]
        
        print(f"\n--- Load Test Results ---")
        print(f"Total Requests: {concurrency}")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Throughput: {concurrency / total_time:.2f} req/s")
        print(f"Avg Latency: {avg_latency:.4f}s")
        print(f"P95 Latency: {p95_latency:.4f}s")
        
        # Ensure it can handle the load reasonably well
        assert len(latencies) == concurrency
