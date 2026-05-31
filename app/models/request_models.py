"""
Request models for the Self-Healing RAG API.

Defines Pydantic models for all incoming API request bodies.
"""

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    """Request body for the POST /ask endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's question to answer using retrieved documents.",
        examples=["Does the text prove that Rama historically existed?"],
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=50,
        description="Override the default number of chunks to retrieve.",
    )
