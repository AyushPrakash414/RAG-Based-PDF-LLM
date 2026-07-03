"""
Response models for the Self-Healing RAG API.

Defines Pydantic models for all outgoing API response bodies.
"""

from pydantic import BaseModel, Field


class AskResponse(BaseModel):
    """Response body for the POST /ask endpoint."""

    answer: str = Field(
        ...,
        description="The generated answer.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Source documents used to generate the answer.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Critic confidence score for the answer.",
    )
    retrieval_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for retrieval relevance.",
    )
    attempts: int = Field(
        ...,
        ge=1,
        description="Number of attempts made by the orchestrator.",
    )
    status: str = Field(
        ...,
        description="Final verdict: APPROVED or REJECTED.",
    )


class HealthResponse(BaseModel):
    """Response body for the POST /health endpoint."""

    api: str = Field(
        default="UP",
        description="API server status.",
    )
    groq: str = Field(
        default="UNKNOWN",
        description="Groq LLM provider status.",
    )
    qdrant: str = Field(
        default="UNKNOWN",
        description="Qdrant vector store status.",
    )


class CriticResult(BaseModel):
    """Structured output from the Answer Critic service."""

    grounded: bool = Field(
        ...,
        description="Whether the answer is grounded in the retrieved context.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the evaluation.",
    )
    reason: str = Field(
        ...,
        description="Explanation of the evaluation verdict.",
    )
    verdict: str = Field(
        ...,
        description="APPROVED or REJECTED.",
    )


class RetrievalValidatorResult(BaseModel):
    """Structured output from the Retrieval Validator service."""

    relevant: bool = Field(
        ...,
        description="Whether the retrieved chunks are relevant to the question.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the relevance evaluation.",
    )
    reason: str = Field(
        ...,
        description="Explanation of the relevance verdict.",
    )


class RetrievalResult(BaseModel):
    """Structured output from the Retrieval Service."""

    chunks: list[str] = Field(
        default_factory=list,
        description="Retrieved text chunks.",
    )
    scores: list[float] = Field(
        default_factory=list,
        description="Similarity scores for each chunk.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Source document names for each chunk.",
    )
    retrieval_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall retrieval confidence (avg of top scores).",
    )

class GenerationResult(BaseModel):
    """Structured output from the Answer Generator."""

    answer: str = Field(
        ...,
        description="The generated answer.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="List of source filenames actually used in the answer.",
    )
