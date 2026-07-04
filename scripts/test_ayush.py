"""Quick test: full pipeline for Ayush question."""
import asyncio, os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dotenv import load_dotenv
load_dotenv()

from app.config.settings import get_settings
from app.providers.groq_provider import GroqProvider
from app.providers.qdrant_vector_store import QdrantVectorStore
from app.services.query_rewriter import QueryRewriter
from app.services.retrieval_validator import RetrievalValidator
from app.services.answer_critic import AnswerCritic
from app.services.answer_generator import AnswerGenerator
from app.services.orchestrator_service import OrchestratorService
from app.services.retrieval_service import RetrievalService
from app.services.retrieval.vector_search_strategy import VectorSearchStrategy

async def main():
    settings = get_settings()
    provider = GroqProvider(settings)
    vector_store = QdrantVectorStore(settings)
    strategy = VectorSearchStrategy(vector_store)
    retrieval_service = RetrievalService(strategy=strategy)
    
    orchestrator = OrchestratorService(
        retrieval_service=retrieval_service,
        retrieval_validator=RetrievalValidator(provider, settings),
        answer_generator=AnswerGenerator(provider, settings),
        answer_critic=AnswerCritic(provider, settings),
        query_rewriter=QueryRewriter(provider, settings),
        settings=settings,
    )

    print("Testing: Who is Ayush Prakash Tiwari")
    print("=" * 60)
    result = await orchestrator.ask("Who is Ayush Prakash Tiwari")
    print(f"Status:     {result.status}")
    print(f"Attempts:   {result.attempts}")
    print(f"Confidence: {result.confidence}")
    print(f"Sources:    {result.sources}")
    print(f"Answer:     {result.answer}")

if __name__ == "__main__":
    asyncio.run(main())
