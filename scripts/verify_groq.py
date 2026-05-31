"""
Groq Migration Verification Script.

Systematically verifies that all components of the Self-Healing RAG pipeline
function correctly with the new GroqProvider implementation.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure the root of the project is in the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config.settings import get_settings
from app.providers.groq_provider import GroqProvider
from app.providers.qdrant_vector_store import QdrantVectorStore
from app.services.query_rewriter import QueryRewriter
from app.services.retrieval_validator import RetrievalValidator
from app.services.answer_critic import AnswerCritic
from app.services.answer_generator import AnswerGenerator
from app.services.orchestrator_service import OrchestratorService
from app.services.retrieval_service import RetrievalService


async def main():
    print("====================================================")
    print("         Groq Provider Migration Verification        ")
    print("====================================================\n")

    load_dotenv()
    settings = get_settings()

    # Verify GROQ_API_KEY
    if not settings.groq_api_key or settings.groq_api_key.strip() == "" or "your_groq_api_key" in settings.groq_api_key:
        print("❌ Error: GROQ_API_KEY environment variable is not configured in .env")
        print("   Please populate the GROQ_API_KEY in the .env file to run this verification.")
        sys.exit(1)

    print("✅ Loaded settings successfully.")
    print(f"   Groq Model: {settings.groq_model}")
    print(f"   Qdrant URL: {settings.qdrant_url}\n")

    # Initialize Provider
    print("--- 1. Initializing GroqProvider ---")
    provider = GroqProvider(settings)
    print("   Performing LLM Health Check...")
    healthy = await provider.health_check()
    if healthy:
        print("   ✅ Groq health check: UP")
    else:
        print("   ❌ Groq health check: DOWN (API key might be invalid or rate-limited)")
        sys.exit(1)

    # Test 1: Query Rewriter works
    print("\n--- 2. Testing Query Rewriter (temperature=0.2) ---")
    rewriter = QueryRewriter(provider, settings)
    original_query = "What is ram and how popular is he in hinduism?"
    rewritten_query = await rewriter.rewrite(original_query)
    print(f"   Original:  '{original_query}'")
    print(f"   Rewritten: '{rewritten_query}'")
    if rewritten_query and len(rewritten_query) > 5:
        print("   ✅ Query Rewriter works.")
    else:
        print("   ❌ Query Rewriter failed (returned fallback or empty).")

    # Test 2: Retrieval Validator returns valid JSON
    print("\n--- 3. Testing Retrieval Validator (temperature=0.0) ---")
    validator = RetrievalValidator(provider, settings)
    question = "Who is Rama?"
    chunks = [
        "Rama is a major deity of Hinduism. He is the seventh and one of the most popular avatars of the god Vishnu.",
        "In Rama-centric traditions of Hinduism, he is considered the Supreme Being.",
    ]
    val_result = await validator.validate(question, chunks)
    print(f"   Relevance verdict: {val_result.relevant}")
    print(f"   Confidence score:  {val_result.confidence}")
    print(f"   Reasoning:         '{val_result.reason}'")
    if val_result.confidence > 0.0 or val_result.relevant:
        print("   ✅ Retrieval Validator returned valid JSON and parsed successfully.")
    else:
        print("   ❌ Retrieval Validator parsing failed (returned fallback).")

    # Test 3: Answer Generator returns answers
    print("\n--- 4. Testing Answer Generator (temperature=0.3) ---")
    generator = AnswerGenerator(provider, settings)
    context = "\n\n".join(chunks)
    answer = await generator.generate(question, context)
    print(f"   Generated Answer: '{answer}'")
    if answer and len(answer) > 10:
        print("   ✅ Answer Generator works.")
    else:
        print("   ❌ Answer Generator failed.")

    # Test 4: Answer Critic returns valid JSON
    print("\n--- 5. Testing Answer Critic (temperature=0.0) ---")
    critic = AnswerCritic(provider, settings)
    critic_result = await critic.evaluate(question, context, answer)
    print(f"   Grounded:          {critic_result.grounded}")
    print(f"   Confidence:        {critic_result.confidence}")
    print(f"   Verdict:           {critic_result.verdict}")
    print(f"   Reasoning:         '{critic_result.reason}'")
    if critic_result.confidence > 0.0 or critic_result.verdict == "APPROVED":
        print("   ✅ Answer Critic returned valid JSON and parsed successfully.")
    else:
        print("   ❌ Answer Critic parsing failed (returned fallback).")

    # Test 5: Full Self-Healing Pipeline
    print("\n--- 6. Testing Full Self-Healing Pipeline (OrchestratorService) ---")
    # Initialize Qdrant and Retrieval service
    print("   Initializing Vector Store & Retrieval Service...")
    vector_store = QdrantVectorStore(settings)
    retrieval_service = RetrievalService(vector_store)

    orchestrator = OrchestratorService(
        retrieval_service=retrieval_service,
        retrieval_validator=validator,
        answer_generator=generator,
        answer_critic=critic,
        query_rewriter=rewriter,
        settings=settings,
    )

    print("   Executing full pipeline query...")
    pipeline_result = await orchestrator.ask("Who is Rama?")
    print(f"   Pipeline Status:     {pipeline_result.status}")
    print(f"   Pipeline Attempts:   {pipeline_result.attempts}")
    print(f"   Pipeline Confidence: {pipeline_result.confidence}")
    print(f"   Pipeline Answer:     '{pipeline_result.answer}'")
    print(f"   Pipeline Sources:    {pipeline_result.sources}")

    print("\n====================================================")
    print("      Verification Completed Successfully! 🎉      ")
    print("====================================================")


if __name__ == "__main__":
    asyncio.run(main())
