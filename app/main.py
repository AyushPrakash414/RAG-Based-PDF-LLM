"""
FastAPI application entry point for the Self-Healing RAG service.

Wires up all services via dependency injection at startup
and mounts the API router.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router, get_orchestrator, get_llm_provider, get_vector_store
from app.config.settings import get_settings, Settings
from app.providers.groq_provider import GroqProvider
from app.providers.qdrant_vector_store import QdrantVectorStore
from app.services.answer_critic import AnswerCritic
from app.services.answer_generator import AnswerGenerator
from app.services.orchestrator_service import OrchestratorService
from app.services.query_rewriter import QueryRewriter
from app.services.retrieval_service import RetrievalService
from app.services.retrieval_validator import RetrievalValidator
from app.utils.logger import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Initialises all services on startup and wires dependency
    injection overrides into the FastAPI router.
    """
    settings: Settings = get_settings()
    setup_logging(level=settings.log_level)

    logger.info("===== Self-Healing RAG Service Starting =====")
    logger.info("Groq model: %s", settings.groq_model)
    logger.info("Qdrant URL: %s", settings.qdrant_url)
    logger.info("Embedding model: %s", settings.embedding_model)
    logger.info("Max retries: %d", settings.max_retries)

    # --- Initialise providers ---
    groq_provider = GroqProvider(settings)
    qdrant_store = QdrantVectorStore(settings)

    # --- Initialise services ---
    retrieval_service = RetrievalService(vector_store=qdrant_store)
    retrieval_validator = RetrievalValidator(
        llm_provider=groq_provider, settings=settings
    )
    answer_generator = AnswerGenerator(
        llm_provider=groq_provider, settings=settings
    )
    answer_critic = AnswerCritic(
        llm_provider=groq_provider, settings=settings
    )
    query_rewriter = QueryRewriter(
        llm_provider=groq_provider, settings=settings
    )

    orchestrator = OrchestratorService(
        retrieval_service=retrieval_service,
        retrieval_validator=retrieval_validator,
        answer_generator=answer_generator,
        answer_critic=answer_critic,
        query_rewriter=query_rewriter,
        settings=settings,
    )

    # --- Wire dependency overrides ---
    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    app.dependency_overrides[get_llm_provider] = lambda: groq_provider
    app.dependency_overrides[get_vector_store] = lambda: qdrant_store

    logger.info("===== All services initialised successfully =====")

    yield

    # --- Shutdown ---
    logger.info("===== Self-Healing RAG Service Shutting Down =====")
    app.dependency_overrides.clear()


# --- Create FastAPI app ---
app = FastAPI(
    title="Self-Healing RAG Service",
    description=(
        "A production-ready Self-Healing Retrieval-Augmented Generation "
        "microservice with multi-stage retry strategies, retrieval validation, "
        "answer grounding evaluation, and full execution tracing."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS middleware (for future React frontend integration) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Mount router ---
app.include_router(router)
