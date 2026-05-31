"""
FastAPI route definitions for the Self-Healing RAG service.

Defines the POST /ask and POST /health endpoints with
proper dependency injection and error handling.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.request_models import AskRequest
from app.models.response_models import AskResponse, HealthResponse
from app.services.orchestrator_service import OrchestratorService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_orchestrator() -> OrchestratorService:
    """
    Dependency stub — replaced at startup in main.py.

    Raises:
        RuntimeError: Always, unless overridden.
    """
    raise RuntimeError("Orchestrator not initialised")


def get_llm_provider():
    """
    Dependency stub — replaced at startup in main.py.

    Raises:
        RuntimeError: Always, unless overridden.
    """
    raise RuntimeError("LLM provider not initialised")


def get_vector_store():
    """
    Dependency stub — replaced at startup in main.py.

    Raises:
        RuntimeError: Always, unless overridden.
    """
    raise RuntimeError("Vector store not initialised")


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a question",
    description="Submit a question to the Self-Healing RAG pipeline.",
)
async def ask_question(
    request: AskRequest,
    orchestrator: Annotated[OrchestratorService, Depends(get_orchestrator)],
) -> AskResponse:
    """
    Process a user question through the self-healing RAG pipeline.

    The orchestrator will retrieve, validate, generate, and critique
    the answer with up to 3 retry attempts using escalating strategies.
    """
    try:
        logger.info("POST /ask received: question='%s'", request.question[:80])
        response = await orchestrator.ask(
            question=request.question,
            top_k_override=request.top_k,
        )
        return response
    except Exception as exc:
        logger.error("POST /ask failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing question: {str(exc)}",
        ) from exc


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health of the API, Groq, and Qdrant.",
)
async def health_check(
    llm_provider=Depends(get_llm_provider),
    vector_store=Depends(get_vector_store),
) -> HealthResponse:
    """
    Check the health status of all service components.

    Returns the status of the API server, Groq LLM provider,
    and Qdrant vector store.
    """
    groq_status = "DOWN"
    qdrant_status = "DOWN"

    try:
        if await llm_provider.health_check():
            groq_status = "UP"
    except Exception as exc:
        logger.warning("Groq health check error: %s", exc)

    try:
        if await vector_store.health_check():
            qdrant_status = "UP"
    except Exception as exc:
        logger.warning("Qdrant health check error: %s", exc)

    return HealthResponse(
        api="UP",
        groq=groq_status,
        qdrant=qdrant_status,
    )
