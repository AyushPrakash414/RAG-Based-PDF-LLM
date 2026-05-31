"""Quick diagnostic: call Gemini with the retrieval validator prompt and print raw output."""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.config.settings import get_settings
from app.providers.gemini_provider import GeminiProvider

settings = get_settings()
gp = GeminiProvider(settings)

prompt = """You are a retrieval quality evaluator.

Question:
about ram?

Retrieved Chunks:
Chunk 1:
Rama is a major deity of Hinduism. He is the seventh and one of the most popular avatars of the god Vishnu.

Evaluation Criteria:
1. Do the retrieved chunks contain information that directly addresses the question?
2. Is there enough relevant content in the chunks to formulate a meaningful answer?

You MUST respond with ONLY a valid JSON object (no markdown, no extra text):

{"relevant": true, "confidence": 0.85, "reason": "brief explanation"}
or
{"relevant": false, "confidence": 0.2, "reason": "brief explanation"}

JSON Response:"""

async def main():
    result = await gp.generate(prompt)
    print("=== RAW RESPONSE ===")
    print(repr(result))
    print("=== DISPLAY ===")
    print(result)

asyncio.run(main())
