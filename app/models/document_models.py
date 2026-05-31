"""
Document models for future upload/management API readiness.

These models define the data structures for a future
document management API (POST /documents/upload, GET /documents,
DELETE /documents/{id}). No endpoints are implemented yet.
"""

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata associated with an ingested document."""

    document_id: str = Field(
        ...,
        description="Unique identifier for the document.",
    )
    filename: str = Field(
        ...,
        description="Original filename of the uploaded document.",
    )
    content_type: str = Field(
        default="text/plain",
        description="MIME type of the document.",
    )
    chunk_count: int = Field(
        default=0,
        ge=0,
        description="Number of chunks the document was split into.",
    )
    file_size_bytes: int = Field(
        default=0,
        ge=0,
        description="Size of the original file in bytes.",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of ingestion.",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary additional metadata.",
    )


class DocumentUploadRequest(BaseModel):
    """Request body for future POST /documents/upload endpoint."""

    filename: str = Field(
        ...,
        min_length=1,
        description="Name of the file being uploaded.",
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Raw text content of the document.",
    )
    content_type: str = Field(
        default="text/plain",
        description="MIME type of the document.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional custom metadata.",
    )


class DocumentUploadResponse(BaseModel):
    """Response body for future POST /documents/upload endpoint."""

    document_id: str = Field(
        ...,
        description="Unique identifier assigned to the document.",
    )
    filename: str = Field(
        ...,
        description="Original filename.",
    )
    chunk_count: int = Field(
        ...,
        description="Number of chunks created.",
    )
    status: str = Field(
        default="INGESTED",
        description="Ingestion status.",
    )


class DocumentListResponse(BaseModel):
    """Response body for future GET /documents endpoint."""

    documents: list[DocumentMetadata] = Field(
        default_factory=list,
        description="List of all ingested documents.",
    )
    total: int = Field(
        default=0,
        description="Total number of documents.",
    )


class DocumentDeleteResponse(BaseModel):
    """Response body for future DELETE /documents/{id} endpoint."""

    document_id: str = Field(
        ...,
        description="ID of the deleted document.",
    )
    chunks_deleted: int = Field(
        default=0,
        description="Number of chunks removed from the vector store.",
    )
    status: str = Field(
        default="DELETED",
        description="Deletion status.",
    )
