"""
Debug script: show what chunks are actually retrieved for a question.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

from app.config.settings import get_settings
from app.providers.qdrant_vector_store import QdrantVectorStore
from app.services.retrieval_service import RetrievalService
from app.services.retrieval.vector_search_strategy import VectorSearchStrategy


async def main():
    settings = get_settings()
    vector_store = QdrantVectorStore(settings)
    strategy = VectorSearchStrategy(vector_store)
    retrieval_service = RetrievalService(strategy=strategy)

    question = "Who is Ayush Prakash Tiwari"
    print(f"Question: {question}")
    print("=" * 80)

    result = await retrieval_service.retrieve(
        question=question,
        k=4,
        score_threshold=0.0,
    )

    print(f"\nRetrieved {len(result.chunks)} chunks")
    print(f"Retrieval confidence: {result.retrieval_confidence:.4f}")
    print(f"Sources: {result.sources}")
    print(f"Scores: {result.scores}")

    for i, (chunk, score, source) in enumerate(
        zip(result.chunks, result.scores, result.sources)
    ):
        print(f"\n--- Chunk {i+1} (score={score:.4f}, source={source}) ---")
        # Show first 500 chars to see quality
        preview = chunk[:500]
        print(preview)
        if len(chunk) > 500:
            print(f"... ({len(chunk)} total chars)")


if __name__ == "__main__":
    asyncio.run(main())
