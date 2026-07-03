"""
FastAPI route definitions for the Self-Healing RAG service.

Defines endpoints for document ingestion, querying, and health checks
with proper dependency injection, validation, and error handling.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form

from app.models.request_models import AskRequest
from app.models.response_models import AskResponse, HealthResponse
from app.services.orchestrator_service import OrchestratorService
from app.services.ingestion_service import get_task, IngestionStatus

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency stubs (replaced at startup in main.py)
# ---------------------------------------------------------------------------

def get_orchestrator() -> OrchestratorService:
    """Dependency stub — replaced at startup in main.py."""
    raise RuntimeError("Orchestrator not initialised")


def get_llm_provider():
    """Dependency stub — replaced at startup in main.py."""
    raise RuntimeError("LLM provider not initialised")


def get_vector_store():
    """Dependency stub — replaced at startup in main.py."""
    raise RuntimeError("Vector store not initialised")


def get_ingestion_service():
    """Dependency stub — replaced at startup in main.py."""
    raise RuntimeError("Ingestion service not initialised")


def get_redis_provider():
    """Dependency stub — replaced at startup in main.py."""
    raise RuntimeError("Redis provider not initialised")


# ---------------------------------------------------------------------------
# Document ingestion endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/documents/ingest",
    summary="Ingest a new document",
    description="Upload a PDF, DOCX, or TXT file to be chunked and stored in the vector database.",
)
async def ingest_document(
    file: UploadFile,
    document_id: str = Form(...),
    ingestion_service=Depends(get_ingestion_service),
    redis_provider=Depends(get_redis_provider),
):
    """Ingest a document synchronously (backward compatible)."""
    try:
        logger.info(
            "POST /documents/ingest received: document_id='%s', filename='%s'",
            document_id,
            file.filename,
        )
        result = await ingestion_service.ingest_file(file, document_id)
        
        # Increment knowledge base version in Redis to invalidate caches
        await redis_provider.increment_knowledge_base_version()
        
        return result
    except ValueError as exc:
        logger.warning("POST /documents/ingest validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("POST /documents/ingest failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing document: {str(exc)}",
        ) from exc


@router.post(
    "/documents/ingest/async",
    summary="Start async document ingestion",
    description="Upload a document and start background processing. Returns a task ID for progress tracking.",
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_document_async(
    file: UploadFile,
    document_id: str = Form(...),
    ingestion_service=Depends(get_ingestion_service),
):
    """Start async ingestion and return task ID immediately."""
    try:
        logger.info(
            "POST /documents/ingest/async received: document_id='%s', filename='%s'",
            document_id,
            file.filename,
        )
        result = await ingestion_service.start_ingestion(file, document_id)
        return result
    except ValueError as exc:
        logger.warning("POST /documents/ingest/async validation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error(
            "POST /documents/ingest/async failed: %s", exc, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing document: {str(exc)}",
        ) from exc


@router.get(
    "/documents/ingest/status/{task_id}",
    summary="Check ingestion task status",
    description="Poll the status of an async ingestion task.",
)
async def get_ingestion_status(task_id: str):
    """Get the current status of an async ingestion task."""
    task = get_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion task '{task_id}' not found",
        )

    return {
        "task_id": task.task_id,
        "document_id": task.document_id,
        "filename": task.filename,
        "status": task.status.value,
        "progress_pct": round(task.progress_pct, 1),
        "chunks_processed": task.chunks_processed,
        "total_chunks": task.total_chunks,
        "error": task.error,
        "result": task.result,
    }


@router.delete(
    "/documents/{document_id}",
    summary="Delete a document",
    description="Delete all vector chunks associated with a document ID from Qdrant.",
)
async def delete_document(
    document_id: str,
    ingestion_service=Depends(get_ingestion_service),
    redis_provider=Depends(get_redis_provider),
):
    """Delete a document and its vector chunks."""
    try:
        logger.info("DELETE /documents/%s received", document_id)
        await ingestion_service.delete_document(document_id)
        
        # Increment knowledge base version in Redis to invalidate caches
        await redis_provider.increment_knowledge_base_version()
        
        return {"status": "success", "message": f"Document {document_id} deleted."}
    except Exception as exc:
        logger.error(
            "DELETE /documents/%s failed: %s", document_id, exc, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error deleting document: {str(exc)}",
        ) from exc


# ---------------------------------------------------------------------------
# Question answering endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a question",
    description="Submit a question to the Self-Healing RAG pipeline.",
)
async def ask_question(
    request: AskRequest,
    orchestrator: Annotated[OrchestratorService, Depends(get_orchestrator)],
    redis_provider=Depends(get_redis_provider),
) -> AskResponse:
    """
    Process a user question through the self-healing RAG pipeline.

    The orchestrator will retrieve, validate, generate, and critique
    the answer with up to 3 retry attempts using escalating strategies.
    """
    try:
        logger.info("POST /ask received: question='%s'", request.question[:80])
        
        # Check Redis Cache
        cached_response_dict = await redis_provider.get_cached_response(request.question)
        if cached_response_dict:
            # Reconstruct AskResponse object from the cached dictionary
            return AskResponse(**cached_response_dict)
        
        response = await orchestrator.ask(
            question=request.question,
            top_k_override=request.top_k,
            allowed_document_ids=request.allowed_document_ids,
        )
        
        # Cache the response
        if response.status == "APPROVED":
            await redis_provider.set_cached_response(request.question, response.model_dump())
            
        return response
    except Exception as exc:
        logger.error("POST /ask failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal error processing question: {str(exc)}",
        ) from exc


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------

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
