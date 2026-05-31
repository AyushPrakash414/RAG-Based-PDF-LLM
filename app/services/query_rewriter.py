"""
Query rewriter service.

Rewrites user questions to improve retrieval quality
by making them more precise and keyword-rich.
"""

import logging

from app.interfaces.llm_provider import LLMProvider
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class QueryRewriter:
    """
    Service responsible for rewriting user queries
    to improve document retrieval effectiveness.
    """

    def __init__(self, llm_provider: LLMProvider, settings: Settings) -> None:
        """
        Initialise the query rewriter.

        Args:
            llm_provider: The LLM provider for rewriting.
            settings: Application settings (for prompt path).
        """
        self._llm = llm_provider
        self._prompt_template = self._load_prompt(settings.prompts_dir)

    @staticmethod
    def _load_prompt(prompts_dir: str) -> str:
        """Load the rewrite prompt template from disk."""
        prompt_path = f"{prompts_dir}/rewrite_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def rewrite(self, question: str) -> str:
        """
        Rewrite a user question for improved retrieval.

        Args:
            question: The original user question.

        Returns:
            The rewritten query string. Falls back to the
            original question if rewriting fails.
        """
        prompt = self._prompt_template.format(question=question)

        try:
            rewritten = await self._llm.generate(prompt, temperature=0.2)
            # Clean up: remove quotes, whitespace, prefixes
            rewritten = rewritten.strip().strip('"').strip("'").strip()

            # If the LLM returned something empty or too short, use original
            if len(rewritten) < 5:
                logger.warning(
                    "Rewritten query too short, using original: '%s'",
                    question[:80],
                )
                return question

            logger.info(
                "Query rewritten: '%s' -> '%s'",
                question[:60],
                rewritten[:80],
            )
            return rewritten

        except Exception as exc:
            logger.error(
                "Query rewriting failed, using original: %s", exc, exc_info=True
            )
            return question
