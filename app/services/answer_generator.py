"""
Answer generator service.

Single responsibility: build a generation prompt from
the question and retrieved context, then call the LLM
to produce an answer.
"""

import logging

from app.interfaces.llm_provider import LLMProvider
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """
    Service responsible for generating answers using
    retrieved context and an LLM provider.
    """

    def __init__(self, llm_provider: LLMProvider, settings: Settings) -> None:
        """
        Initialise the answer generator.

        Args:
            llm_provider: The LLM provider for generation.
            settings: Application settings (for prompt path).
        """
        self._llm = llm_provider
        self._prompt_template = self._load_prompt(settings.prompts_dir)

    @staticmethod
    def _load_prompt(prompts_dir: str) -> str:
        """Load the generation prompt template from disk."""
        prompt_path = f"{prompts_dir}/generation_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def generate(self, question: str, context: str) -> str:
        """
        Generate an answer for the question using the provided context.

        Args:
            question: The user's question.
            context: The concatenated retrieved chunks.

        Returns:
            The generated answer text.

        Raises:
            RuntimeError: If generation fails.
        """
        prompt = self._prompt_template.format(
            question=question,
            context=context,
        )

        logger.info(
            "Generating answer for question: '%s' (context length: %d chars)",
            question[:80],
            len(context),
        )

        try:
            answer = await self._llm.generate(prompt, temperature=0.3)
            logger.info(
                "Answer generated (%d chars)",
                len(answer),
            )
            return answer
        except Exception as exc:
            logger.error("Answer generation failed: %s", exc, exc_info=True)
            raise
