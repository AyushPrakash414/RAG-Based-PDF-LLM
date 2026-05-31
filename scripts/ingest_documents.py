"""
Document ingestion script.

Loads TXT documents from the documents/ directory,
chunks them using RecursiveCharacterTextSplitter,
generates embeddings, and upserts into Qdrant.

Usage:
    python -m scripts.ingest_documents
    python scripts/ingest_documents.py
"""

import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv

# Ensure the project root is on sys.path so app imports work
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import get_settings
from app.providers.qdrant_vector_store import QdrantVectorStore


def load_documents(doc_dir: Path) -> list:
    """
    Load all .txt documents from the given directory.

    Args:
        doc_dir: Path to the documents directory.

    Returns:
        A list of LangChain Document objects.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not doc_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {doc_dir}")

    loader = DirectoryLoader(
        path=str(doc_dir),
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"[INFO] Loaded {len(documents)} document(s) from {doc_dir}")
    return documents


def chunk_documents(
    documents: list,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list:
    """
    Split documents into smaller chunks for embedding.

    Args:
        documents: LangChain Document objects.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Character overlap between adjacent chunks.

    Returns:
        A list of chunked Document objects.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    print(f"[INFO] Created {len(chunks)} chunk(s)")
    return chunks


def main() -> None:
    """Run the full ingestion pipeline."""
    settings = get_settings()

    # Resolve documents directory
    doc_dir = PROJECT_ROOT / settings.documents_dir
    print(f"[INFO] Documents directory: {doc_dir}")
    print(f"[INFO] Qdrant URL: {settings.qdrant_url}")
    print(f"[INFO] Embedding model: {settings.embedding_model}")

    # Step 1: Load documents
    documents = load_documents(doc_dir)
    if not documents:
        print("[WARN] No documents found. Exiting.")
        return

    # Step 2: Chunk documents
    chunks = chunk_documents(documents)

    # Step 3: Prepare data for Qdrant
    texts: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    for idx, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "unknown")
        # Use just the filename, not the full path
        source_name = Path(source).name

        chunk_id = str(uuid.uuid4())
        document_id = str(uuid.uuid5(uuid.NAMESPACE_URL, source_name))

        texts.append(chunk.page_content)
        metadatas.append(
            {
                "source": source_name,
                "chunk_id": idx,
                "document_id": document_id,
            }
        )
        ids.append(chunk_id)

    # Step 4: Generate embeddings
    print("[INFO] Generating embeddings...")
    vector_store = QdrantVectorStore(settings)
    embeddings = vector_store.embed_texts(texts)
    print(f"[INFO] Generated {len(embeddings)} embedding(s)")

    # Step 5: Upsert into Qdrant (sync wrapper for script use)
    import asyncio

    async def upsert():
        await vector_store.add_documents(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    asyncio.run(upsert())

    print(f"[INFO] Successfully ingested {len(texts)} chunks into Qdrant")
    print("[INFO] Collection: " + settings.qdrant_collection_name)
    print("[DONE] Ingestion complete.")


if __name__ == "__main__":
    main()
