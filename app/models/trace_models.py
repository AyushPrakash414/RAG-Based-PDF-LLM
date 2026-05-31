"""
Trace models for observability and debugging.

Captures the full execution trace of each /ask request,
including retrieval, validation, generation, and critic steps.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from app.models.response_models import CriticResult, RetrievalValidatorResult


class AttemptTrace(BaseModel):
    """Trace data for a single orchestrator attempt."""

    attempt_number: int = Field(
        ...,
        description="The attempt number (1-indexed).",
    )
    query_used: str = Field(
        ...,
        description="The query used for retrieval (original or rewritten).",
    )
    top_k_used: int = Field(
        ...,
        description="Number of chunks requested.",
    )
    similarity_threshold: float = Field(
        ...,
        description="Similarity threshold used for this attempt.",
    )
    retrieval_strategy_used: str = Field(
        default="default",
        description="Strategy label (e.g., 'default', 'expanded', 'aggressive').",
    )
    retrieved_chunks_count: int = Field(
        default=0,
        description="Number of chunks actually retrieved.",
    )
    retrieval_scores: list[float] = Field(
        default_factory=list,
        description="Similarity scores from retrieval.",
    )
    retrieval_confidence: float = Field(
        default=0.0,
        description="Overall retrieval confidence.",
    )
    retrieval_sources: list[str] = Field(
        default_factory=list,
        description="Source documents from retrieval.",
    )
    retrieval_validator_result: RetrievalValidatorResult | None = Field(
        default=None,
        description="Retrieval validation output.",
    )
    generated_answer: str | None = Field(
        default=None,
        description="The generated answer (if generation was reached).",
    )
    critic_result: CriticResult | None = Field(
        default=None,
        description="Critic evaluation output (if critic was reached).",
    )


class RagTrace(BaseModel):
    """
    Full execution trace for a single /ask request.

    Persisted to traces/{request_id}.json for debugging
    and observability.
    """

    request_id: str = Field(
        ...,
        description="Unique identifier for this request.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of the request.",
    )
    original_question: str = Field(
        ...,
        description="The original question from the user.",
    )
    rewritten_queries: list[str] = Field(
        default_factory=list,
        description="All rewritten queries generated during retries.",
    )
    attempts: list[AttemptTrace] = Field(
        default_factory=list,
        description="Trace data for each attempt.",
    )
    total_attempts: int = Field(
        default=0,
        description="Total number of attempts made.",
    )
    final_answer: str | None = Field(
        default=None,
        description="The final answer returned to the user.",
    )
    final_sources: list[str] = Field(
        default_factory=list,
        description="Sources used in the final answer.",
    )
    final_confidence: float = Field(
        default=0.0,
        description="Final critic confidence.",
    )
    final_retrieval_confidence: float = Field(
        default=0.0,
        description="Final retrieval confidence.",
    )
    final_verdict: str = Field(
        default="REJECTED",
        description="Final verdict: APPROVED or REJECTED.",
    )
    duration_ms: float | None = Field(
        default=None,
        description="Total processing time in milliseconds.",
    )
