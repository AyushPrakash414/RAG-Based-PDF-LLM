"""
Retrieval validator service.

Evaluates whether retrieved chunks are actually relevant
to the user's question BEFORE answer generation, enabling
early retry without wasting an LLM generation call.
"""

import logging

from app.interfaces.llm_provider import LLMProvider
from app.models.response_models import RetrievalValidatorResult
from app.config.settings import Settings
from app.utils.json_parser import parse_structured_json

logger = logging.getLogger(__name__)

_DEFAULT_FALLBACK = RetrievalValidatorResult(
    relevant=False,
    confidence=0.0,
    reason="Failed to parse retrieval validation response.",
)


class RetrievalValidator:
    """
    Service responsible for validating whether retrieved chunks
    are relevant to the user's question.
    """

    def __init__(self, llm_provider: LLMProvider, settings: Settings) -> None:
        """
        Initialise the retrieval validator.

        Args:
            llm_provider: The LLM provider for evaluation.
            settings: Application settings (for prompt path).
        """
        self._llm = llm_provider
        self._prompt_template = self._load_prompt(settings.prompts_dir)

    @staticmethod
    def _load_prompt(prompts_dir: str) -> str:
        """Load the retrieval validator prompt template from disk."""
        prompt_path = f"{prompts_dir}/retrieval_validator_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def validate(
        self,
        question: str,
        chunks: list[str],
    ) -> RetrievalValidatorResult:
        """
        Evaluate whether the retrieved chunks are relevant to the question.

        Args:
            question: The user's question.
            chunks: The retrieved text chunks.

        Returns:
            A RetrievalValidatorResult with relevance, confidence, and reason.
        """
        if not chunks:
            return RetrievalValidatorResult(
                relevant=False,
                confidence=0.0,
                reason="No chunks were retrieved.",
            )

        # Format chunks for the prompt
        formatted_chunks = "\n\n---\n\n".join(
            f"Chunk {i + 1}:\n{chunk}" for i, chunk in enumerate(chunks)
        )

        prompt = self._prompt_template.format(
            question=question,
            chunks=formatted_chunks,
        )

        try:
            raw_response = await self._llm.generate(prompt, temperature=0.0, json_mode=True)
            logger.debug("Validator raw response: %s", raw_response[:500])
            result = parse_structured_json(raw_response, RetrievalValidatorResult)
            logger.info(
                "Retrieval validation: relevant=%s, confidence=%.2f, reason='%s'",
                result.relevant,
                result.confidence,
                result.reason[:100],
            )
            return result
        except Exception as exc:
            logger.error(
                "Retrieval validation failed: %s", exc, exc_info=True
            )
            return _DEFAULT_FALLBACK

