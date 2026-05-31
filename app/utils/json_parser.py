"""
Robust JSON parsing utility for LLM responses.

Ensures strict validation against Pydantic models and handles markdown code blocks,
extra conversational filler, and other common LLM outputs.
"""

import json
import re
import logging
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class JSONParsingError(ValueError):
    """Exception raised when JSON extraction, parsing, or Pydantic validation fails."""

    pass


def parse_structured_json(text: str, model_class: Type[T]) -> T:
    """
    Parse a raw LLM text response into a validated Pydantic model instance.

    Attempts multiple strategies:
      1. Direct JSON parsing of the entire text.
      2. Automated stripping of markdown code fences (```json ... ``` or ``` ... ```) and retry.
      3. Scanning and extracting the first matched brace group '{...}' as a final fallback.

    Args:
        text: The raw response text string from the LLM.
        model_class: The Pydantic model class to validate and instantiate.

    Returns:
        An instance of `model_class`.

    Raises:
        JSONParsingError: If all parsing strategies and validations fail.
    """
    if not text:
        raise JSONParsingError("Cannot parse empty or null response.")

    cleaned_text = text.strip()

    # --- Strategy 1: Direct JSON Parse ---
    try:
        data = json.loads(cleaned_text)
        return model_class.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.debug(
            "Direct parsing failed or Pydantic validation failed: %s. Attempting markdown/brace cleanup.",
            exc,
        )

    # --- Strategy 2: Strip Markdown Code Blocks & Retry ---
    # This automatically matches and extracts everything between the ``` or ```json fences
    fenced_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned_text, re.DOTALL)
    if fenced_match:
        fenced_json = fenced_match.group(1).strip()
        try:
            data = json.loads(fenced_json)
            return model_class.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.debug(
                "Markdown-fenced parsing failed or validation failed: %s. Attempting brace extraction.",
                exc,
            )

    # --- Strategy 3: Extract first outer '{...}' brace block ---
    brace_match = re.search(r"(\{.*\})", cleaned_text, re.DOTALL)
    if brace_match:
        braced_json = brace_match.group(1).strip()
        try:
            data = json.loads(braced_json)
            return model_class.model_validate(data)
        except json.JSONDecodeError as exc:
            raise JSONParsingError(
                f"Brace-extracted text is not valid JSON. Error: {exc}. "
                f"Extracted content: {repr(braced_json)}"
            ) from exc
        except ValidationError as exc:
            raise JSONParsingError(
                f"Brace-extracted JSON is valid but failed Pydantic validation for {model_class.__name__}. "
                f"Error: {exc}. Extracted data: {data}"
            ) from exc

    # If all options are exhausted, raise a highly descriptive error
    raise JSONParsingError(
        f"Failed to extract or validate structured JSON for Pydantic model {model_class.__name__} from LLM response. "
        f"Raw response: {repr(cleaned_text)}"
    )
