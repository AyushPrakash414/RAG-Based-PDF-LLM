"""
FastAPI application entry point for the Self-Healing RAG service.

Wires up all services via dependency injection at startup
and mounts the API router with security middleware.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router, get_orchestrator, get_llm_provider, get_vector_store, get_ingestion_service
from app.config.settings import get_settings, Settings
from app.middleware import ServiceAuthMiddleware
from app.providers.groq_provider import GroqProvider
from app.providers.qdrant_vector_store import QdrantVectorStore
from app.services.answer_critic import AnswerCritic
from app.services.answer_generator import AnswerGenerator
from app.services.orchestrator_service import OrchestratorService
from app.services.query_rewriter import QueryRewriter
from app.services.retrieval_service import RetrievalService
from app.services.retrieval.vector_search_strategy import VectorSearchStrategy
from app.services.retrieval_validator import RetrievalValidator
from app.services.ingestion_service import IngestionService
from app.services.spell_corrector import SpellCorrector
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
    logger.info(
        "Internal API auth: %s",
        "ENABLED" if settings.internal_api_secret else "DISABLED",
    )

    # --- Initialise providers ---
    groq_provider = GroqProvider(settings)
    qdrant_store = QdrantVectorStore(settings)

    # --- Initialise services ---
    spell_corrector = SpellCorrector(max_edit_distance=2)
    vector_strategy = VectorSearchStrategy(qdrant_store)
    retrieval_service = RetrievalService(
        strategy=vector_strategy,
        spell_corrector=spell_corrector,
    )
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
    ingestion_service = IngestionService(vector_store=qdrant_store)

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
    app.dependency_overrides[get_ingestion_service] = lambda: ingestion_service

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

# --- Security: HMAC service-to-service authentication ---
_settings = get_settings()
if _settings.internal_api_secret:
    app.add_middleware(ServiceAuthMiddleware, secret=_settings.internal_api_secret)
    logger.info("HMAC service authentication middleware enabled")
else:
    logger.warning(
        "INTERNAL_API_SECRET not set — service auth middleware DISABLED. "
        "Set INTERNAL_API_SECRET in .env for production deployments."
    )

# --- CORS middleware ---
_allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# --- Mount router ---
app.include_router(router)
