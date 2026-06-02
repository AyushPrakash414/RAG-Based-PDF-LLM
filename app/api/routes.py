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


def get_ingestion_service():
    """
    Dependency stub — replaced at startup in main.py.
    """
    raise RuntimeError("Ingestion service not initialised")


from fastapi import UploadFile, Form

@router.post(
    "/documents/ingest",
    summary="Ingest a new document",
    description="Upload a PDF, DOCX, or TXT file to be chunked and stored in the vector database.",
)
async def ingest_document(
    file: UploadFile,
    document_id: str = Form(...),
    ingestion_service=Depends(get_ingestion_service),
):
    try:
        logger.info("POST /documents/ingest received: document_id='%s', filename='%s'", document_id, file.filename)
        result = await ingestion_service.ingest_file(file, document_id)
        return result
    except Exception as exc:
        logger.error("POST /documents/ingest failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing document: {str(exc)}",
        ) from exc


@router.delete(
    "/documents/{document_id}",
    summary="Delete a document",
    description="Delete all vector chunks associated with a document ID from Qdrant.",
)
async def delete_document(
    document_id: str,
    ingestion_service=Depends(get_ingestion_service),
):
    try:
        logger.info("DELETE /documents/%s received", document_id)
        await ingestion_service.delete_document(document_id)
        return {"status": "success", "message": f"Document {document_id} deleted."}
    except Exception as exc:
        logger.error("DELETE /documents/%s failed: %s", document_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error deleting document: {str(exc)}",
        ) from exc


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
            allowed_document_ids=request.allowed_document_ids,
        )
        return response
    except Exception as exc:
        logger.error("POST /ask failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing question: {str(exc)}",
        ) from exc


@router.api_route(
    "/health",
    methods=["GET", "HEAD"],
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
