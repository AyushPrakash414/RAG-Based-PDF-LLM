"""
Groq LLM provider implementation.

Implements the LLMProvider interface using the official Groq Python SDK.
"""

import asyncio
import logging
import time
import re
from groq import AsyncGroq, RateLimitError

from app.interfaces.llm_provider import LLMProvider
from app.config.settings import Settings

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """
    Concrete LLM provider backed by Groq.

    Wraps the official groq SDK to fulfill the
    LLMProvider contract with async support.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialise the Groq provider.

        Args:
            settings: Application settings containing the API key and model config.
        """
        self._settings = settings
        self._client = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.groq_model
        logger.info(
            "GroqProvider initialised with model=%s",
            self._model,
        )

    async def generate(self, prompt: str, temperature: float | None = None) -> str:
        """
        Generate a response from Groq for the given prompt.

        Args:
            prompt: The full prompt string.
            temperature: Optional override for temperature.

        Returns:
            The generated text.

        Raises:
            RuntimeError: If the Groq API call fails.
        """
        # Determine temperature (defaulting to the configured base temperature if none specified)
        temp = temperature if temperature is not None else self._settings.groq_temperature

        start_time = time.perf_counter()
        logger.debug(
            "Sending prompt to Groq (%d chars) | model=%s | temperature=%.2f",
            len(prompt),
            self._model,
            temp,
        )

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                # Execute completion asynchronously using AsyncGroq client
                response = await self._client.chat.completions.create(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    model=self._model,
                    temperature=temp,
                )
                text = response.choices[0].message.content.strip()
                latency_ms = (time.perf_counter() - start_time) * 1000

                logger.info(
                    "Groq request successful | model=%s | latency=%.2fms | response_len=%d",
                    self._model,
                    latency_ms,
                    len(text),
                )
                return text
            except RateLimitError as exc:
                if attempt < max_attempts:
                    # Try to extract the wait time from the error message
                    error_msg = str(exc)
                    wait_time = 10.0  # default wait time
                    match = re.search(r"try again in ([0-9.]+)s", error_msg)
                    if match:
                        wait_time = float(match.group(1)) + 1.0  # add 1s buffer
                    
                    logger.warning(
                        "Groq rate limit hit (Attempt %d/%d). Waiting %.2fs before retrying...",
                        attempt, max_attempts, wait_time
                    )
                    await asyncio.sleep(wait_time)
                else:
                    latency_ms = (time.perf_counter() - start_time) * 1000
                    logger.error(
                        "Groq rate limit exhausted after %d attempts | model=%s | latency=%.2fms | error=%s",
                        max_attempts,
                        self._model,
                        latency_ms,
                        exc,
                    )
                    raise RuntimeError(f"Groq generation failed due to rate limits: {exc}") from exc
            except Exception as exc:
                latency_ms = (time.perf_counter() - start_time) * 1000
                logger.error(
                    "Groq request failed | model=%s | latency=%.2fms | error=%s",
                    self._model,
                    latency_ms,
                    exc,
                    exc_info=True,
                )
                raise RuntimeError(f"Groq generation failed: {exc}") from exc

    async def health_check(self) -> bool:
        """
        Verify Groq is reachable by sending a minimal prompt.

        Returns:
            True if a response is received, False otherwise.
        """
        start_time = time.perf_counter()
        try:
            response = await self._client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": "Reply with OK",
                    }
                ],
                model=self._model,
                temperature=0.0,
                max_tokens=5,
            )
            text = response.choices[0].message.content
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "Groq health check successful | model=%s | latency=%.2fms",
                self._model,
                latency_ms,
            )
            return bool(text)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.warning(
                "Groq health check failed | model=%s | latency=%.2fms | error=%s",
                self._model,
                latency_ms,
                exc,
            )
            return False
