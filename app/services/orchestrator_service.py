"""
Self-Healing RAG Orchestrator Service.

Manages the multi-stage self-healing workflow:
  Attempt 1: Retrieve(k=4)   → Validate → Generate → Critic
  Attempt 2: Rewrite → Retrieve(k=8)  → Validate → Generate → Critic
  Attempt 3: Rewrite → Retrieve(k=12, lower threshold) → Validate → Generate → Critic
  Fallback:  Return insufficient-information message.

Produces a full RagTrace for every request.
"""

import json
import logging
import time
import uuid
from pathlib import Path

from app.config.settings import Settings
from app.models.response_models import AskResponse, RetrievalResult
from app.models.trace_models import AttemptTrace, RagTrace
from app.services.answer_critic import AnswerCritic
from app.services.answer_generator import AnswerGenerator
from app.services.query_rewriter import QueryRewriter
from app.services.retrieval_service import RetrievalService
from app.services.retrieval_validator import RetrievalValidator

logger = logging.getLogger(__name__)

_FALLBACK_ANSWER = (
    "I do not have enough information in the provided documents "
    "to answer reliably."
)

# Per-attempt retrieval strategies
_STRATEGIES: list[dict] = [
    {
        "label": "default",
        "top_k": 4,
        "threshold_delta": 0.0,
        "rewrite": False,
    },
    {
        "label": "expanded",
        "top_k": 8,
        "threshold_delta": 0.0,
        "rewrite": True,
    },
    {
        "label": "aggressive",
        "top_k": 12,
        "threshold_delta": -0.10,  # lower the threshold
        "rewrite": True,
    },
]


class OrchestratorService:
    """
    Central orchestrator that coordinates the self-healing RAG pipeline.

    Injects all subordinate services and manages the retry loop,
    trace persistence, and final response assembly.
    """

    def __init__(
        self,
        retrieval_service: RetrievalService,
        retrieval_validator: RetrievalValidator,
        answer_generator: AnswerGenerator,
        answer_critic: AnswerCritic,
        query_rewriter: QueryRewriter,
        settings: Settings,
    ) -> None:
        """
        Initialise the orchestrator with all required services.

        Args:
            retrieval_service: Service for vector store retrieval.
            retrieval_validator: Service for validating retrieval relevance.
            answer_generator: Service for LLM answer generation.
            answer_critic: Service for answer grounding evaluation.
            query_rewriter: Service for query rewriting.
            settings: Application settings.
        """
        self._retrieval = retrieval_service
        self._validator = retrieval_validator
        self._generator = answer_generator
        self._critic = answer_critic
        self._rewriter = query_rewriter
        self._settings = settings
        self._max_retries = min(settings.max_retries, len(_STRATEGIES))

    async def ask(
        self, 
        question: str, 
        top_k_override: int | None = None, 
        allowed_document_ids: list[str] | None = None
    ) -> AskResponse:
        """
        Process a user question through the self-healing pipeline.

        Args:
            question: The user's original question.
            top_k_override: Optional override for the base top_k.
            allowed_document_ids: List of document IDs the user is allowed to search.

        Returns:
            An AskResponse with the answer, sources, confidence, and status.
        """
        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        trace = RagTrace(
            request_id=request_id,
            original_question=question,
        )

        logger.info(
            "Orchestrator started | request_id=%s | question='%s'",
            request_id,
            question[:80],
        )

        current_query = question
        final_answer = _FALLBACK_ANSWER
        final_sources: list[str] = []
        final_confidence = 0.0
        final_retrieval_confidence = 0.0
        final_verdict = "REJECTED"

        for attempt_idx in range(self._max_retries):
            strategy = _STRATEGIES[attempt_idx]
            attempt_number = attempt_idx + 1

            logger.info(
                "--- Attempt %d/%d | strategy=%s ---",
                attempt_number,
                self._max_retries,
                strategy["label"],
            )

            # ----- Step 1: Optionally rewrite the query -----
            if strategy["rewrite"] and attempt_idx > 0:
                current_query = await self._rewriter.rewrite(question)
                trace.rewritten_queries.append(current_query)
                logger.info("Rewritten query: '%s'", current_query[:80])

            # ----- Step 2: Determine retrieval params -----
            top_k = top_k_override if top_k_override else strategy["top_k"]
            threshold = max(
                0.0,
                self._settings.similarity_threshold + strategy["threshold_delta"],
            )

            # ----- Step 3: Retrieve -----
            retrieval_result: RetrievalResult = await self._retrieval.retrieve(
                question=current_query,
                k=top_k,
                score_threshold=threshold,
                allowed_document_ids=allowed_document_ids,
            )

            # Initialise attempt trace
            attempt_trace = AttemptTrace(
                attempt_number=attempt_number,
                query_used=current_query,
                top_k_used=top_k,
                similarity_threshold=threshold,
                retrieval_strategy_used=strategy["label"],
                retrieved_chunks_count=len(retrieval_result.chunks),
                retrieval_scores=retrieval_result.scores,
                retrieval_confidence=retrieval_result.retrieval_confidence,
                retrieval_sources=retrieval_result.sources,
            )

            # ----- Step 4: Validate retrieval -----
            if not retrieval_result.chunks:
                logger.warning("No chunks retrieved, skipping to next attempt.")
                trace.attempts.append(attempt_trace)
                continue

            validation_result = await self._validator.validate(
                question=current_query,
                chunks=retrieval_result.chunks,
            )
            attempt_trace.retrieval_validator_result = validation_result

            if not validation_result.relevant:
                logger.warning(
                    "Retrieval validation FAILED (confidence=%.2f): %s",
                    validation_result.confidence,
                    validation_result.reason[:100],
                )
                trace.attempts.append(attempt_trace)
                continue

            # ----- Step 5: Generate answer -----
            context = "\n\n".join(retrieval_result.chunks)
            try:
                answer = await self._generator.generate(
                    question=current_query,
                    context=context,
                )
            except Exception as exc:
                logger.error("Generation failed on attempt %d: %s", attempt_number, exc)
                trace.attempts.append(attempt_trace)
                continue

            attempt_trace.generated_answer = answer

            # ----- Step 6: Critic evaluation -----
            critic_result = await self._critic.evaluate(
                question=current_query,
                context=context,
                answer=answer,
            )
            attempt_trace.critic_result = critic_result

            trace.attempts.append(attempt_trace)

            # ----- Step 7: Check verdict -----
            if critic_result.verdict == "APPROVED":
                final_answer = answer
                final_sources = list(set(retrieval_result.sources))
                final_confidence = critic_result.confidence
                final_retrieval_confidence = retrieval_result.retrieval_confidence
                final_verdict = "APPROVED"
                logger.info(
                    "Answer APPROVED on attempt %d (confidence=%.2f)",
                    attempt_number,
                    critic_result.confidence,
                )
                break
            else:
                logger.warning(
                    "Answer REJECTED on attempt %d (confidence=%.2f): %s",
                    attempt_number,
                    critic_result.confidence,
                    critic_result.reason[:100],
                )
        else:
            # All attempts exhausted
            logger.warning(
                "All %d attempts exhausted. Returning fallback answer.",
                self._max_retries,
            )
            # Append fallback trace if not already present
            if not trace.attempts or trace.attempts[-1] not in trace.attempts:
                pass  # attempts already appended in the loop

        # ----- Finalise trace -----
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        trace.total_attempts = len(trace.attempts)
        trace.final_answer = final_answer
        trace.final_sources = final_sources
        trace.final_confidence = final_confidence
        trace.final_retrieval_confidence = final_retrieval_confidence
        trace.final_verdict = final_verdict
        trace.duration_ms = round(elapsed_ms, 2)

        # Persist trace
        await self._persist_trace(trace)

        logger.info(
            "Orchestrator complete | request_id=%s | verdict=%s | attempts=%d | "
            "confidence=%.2f | duration=%.0fms",
            request_id,
            final_verdict,
            trace.total_attempts,
            final_confidence,
            elapsed_ms,
        )

        return AskResponse(
            answer=final_answer,
            sources=final_sources,
            confidence=final_confidence,
            retrieval_confidence=final_retrieval_confidence,
            attempts=trace.total_attempts,
            status=final_verdict,
        )

    async def _persist_trace(self, trace: RagTrace) -> None:
        """
        Save the execution trace to a JSON file.

        Args:
            trace: The complete RagTrace to persist.
        """
        try:
            traces_dir = Path(self._settings.traces_dir)
            traces_dir.mkdir(parents=True, exist_ok=True)

            trace_path = traces_dir / f"{trace.request_id}.json"
            trace_data = trace.model_dump(mode="json")

            with open(trace_path, "w", encoding="utf-8") as f:
                json.dump(trace_data, f, indent=2, ensure_ascii=False)

            logger.debug("Trace persisted to %s", trace_path)
        except Exception as exc:
            logger.error(
                "Failed to persist trace %s: %s",
                trace.request_id,
                exc,
                exc_info=True,
            )
