"""
Answer critic service.

Evaluates whether a generated answer is properly grounded
in the retrieved context, returning a structured verdict.
"""

import logging

from app.interfaces.llm_provider import LLMProvider
from app.models.response_models import CriticResult
from app.config.settings import Settings
from app.utils.json_parser import parse_structured_json

logger = logging.getLogger(__name__)

_DEFAULT_FALLBACK = CriticResult(
    grounded=False,
    confidence=0.0,
    reason="Failed to parse critic response.",
    verdict="REJECTED",
)


class AnswerCritic:
    """
    Service responsible for evaluating whether a generated
    answer is grounded in the retrieved context.
    """

    def __init__(self, llm_provider: LLMProvider, settings: Settings) -> None:
        """
        Initialise the answer critic.

        Args:
            llm_provider: The LLM provider for evaluation.
            settings: Application settings (for prompt path and thresholds).
        """
        self._llm = llm_provider
        self._settings = settings
        self._prompt_template = self._load_prompt(settings.prompts_dir)

    @staticmethod
    def _load_prompt(prompts_dir: str) -> str:
        """Load the critic prompt template from disk."""
        prompt_path = f"{prompts_dir}/critic_prompt.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    async def evaluate(
        self,
        question: str,
        context: str,
        answer: str,
    ) -> CriticResult:
        """
        Evaluate whether the answer is grounded in the context.

        Args:
            question: The user's question.
            context: The retrieved context used for generation.
            answer: The generated answer to evaluate.

        Returns:
            A CriticResult with grounded, confidence, reason, and verdict.
        """
        prompt = self._prompt_template.format(
            question=question,
            context=context,
            answer=answer,
        )

        try:
            raw_response = await self._llm.generate(prompt, temperature=0.0)
            logger.debug("Critic raw response: %s", raw_response[:500])
            result = parse_structured_json(raw_response, CriticResult)
            logger.info(
                "Critic evaluation: verdict=%s, confidence=%.2f, grounded=%s",
                result.verdict,
                result.confidence,
                result.grounded,
            )
            return result
        except Exception as exc:
            logger.error(
                "Critic evaluation failed: %s", exc, exc_info=True
            )
            return _DEFAULT_FALLBACK

