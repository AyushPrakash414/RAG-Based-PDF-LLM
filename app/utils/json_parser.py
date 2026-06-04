"""
Robust JSON parsing utility for LLM responses.

Implements a 4-layer parsing pipeline:
  1. Extraction Layer — multiple strategies to locate JSON in raw text
  2. Validation Layer — Pydantic model validation with coercion
  3. Recovery Layer — fixes common JSON malformations
  4. Fallback Layer — regex key-value extraction as last resort
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


# ---------------------------------------------------------------------------
# Recovery helpers
# ---------------------------------------------------------------------------

def _fix_trailing_commas(text: str) -> str:
    """Remove trailing commas before closing braces/brackets."""
    return re.sub(r",\s*([}\]])", r"\1", text)


def _fix_single_quotes(text: str) -> str:
    """Replace single quotes used as JSON delimiters with double quotes."""
    # Only replace single quotes that look like JSON string delimiters
    # This is a best-effort heuristic
    result = []
    in_double = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == '"' and (i == 0 or text[i - 1] != '\\'):
            in_double = not in_double
            result.append(ch)
        elif ch == "'" and not in_double:
            result.append('"')
        else:
            result.append(ch)
        i += 1
    return "".join(result)


def _fix_unquoted_keys(text: str) -> str:
    """Quote unquoted JSON keys."""
    return re.sub(
        r'(?<=[{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:',
        r' "\1":',
        text,
    )


def _fix_newlines_in_strings(text: str) -> str:
    """Escape literal newlines inside JSON string values."""
    return re.sub(
        r'(?<=": ")(.*?)(?="[,}\]])',
        lambda m: m.group(0).replace("\n", "\\n"),
        text,
        flags=re.DOTALL,
    )


def _balance_braces(text: str) -> str:
    """Attempt to balance braces for truncated JSON."""
    open_braces = text.count("{") - text.count("}")
    open_brackets = text.count("[") - text.count("]")
    # Close brackets first (inner), then braces (outer)
    if open_brackets > 0:
        text = text.rstrip().rstrip(",") + "]" * open_brackets
    if open_braces > 0:
        text = text.rstrip().rstrip(",") + "}" * open_braces
    return text


def _fix_boolean_none(text: str) -> str:
    """Convert Python-style True/False/None to JSON true/false/null."""
    text = re.sub(r'\bTrue\b', 'true', text)
    text = re.sub(r'\bFalse\b', 'false', text)
    text = re.sub(r'\bNone\b', 'null', text)
    return text


_RECOVERY_PIPELINE = [
    _fix_trailing_commas,
    _fix_single_quotes,
    _fix_unquoted_keys,
    _fix_newlines_in_strings,
    _fix_boolean_none,
    _balance_braces,
]


# ---------------------------------------------------------------------------
# Extraction strategies
# ---------------------------------------------------------------------------

def _extract_candidates(text: str) -> list[str]:
    """
    Generate candidate JSON strings from raw LLM output using multiple
    extraction strategies, ordered from most to least precise.
    """
    candidates: list[str] = []
    cleaned = text.strip()

    # Strategy 1: Direct — entire text might be valid JSON
    candidates.append(cleaned)

    # Strategy 2: Markdown fenced ```json ... ``` or ``` ... ```
    for m in re.finditer(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL):
        candidates.append(m.group(1).strip())

    # Strategy 3: "json" prefix without backticks (e.g., "json\n{...}")
    json_prefix = re.search(r"^json\s*\n(.*)", cleaned, re.DOTALL | re.IGNORECASE)
    if json_prefix:
        candidates.append(json_prefix.group(1).strip())

    # Strategy 4: First outer brace block with balanced matching
    brace_depth = 0
    start_idx = -1
    for i, ch in enumerate(cleaned):
        if ch == '{':
            if brace_depth == 0:
                start_idx = i
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            if brace_depth == 0 and start_idx >= 0:
                candidates.append(cleaned[start_idx:i + 1])
                break

    # Strategy 5: Greedy brace match (fallback if balanced matching misses)
    greedy = re.search(r"(\{.*\})", cleaned, re.DOTALL)
    if greedy:
        candidates.append(greedy.group(1).strip())

    # Strategy 6: Array extraction [...]
    arr = re.search(r"(\[.*\])", cleaned, re.DOTALL)
    if arr:
        candidates.append(arr.group(1).strip())

    # Strategy 7: Multiple JSON objects — take the last one (often the final answer)
    all_braces = list(re.finditer(r"\{[^{}]*\}", cleaned))
    if len(all_braces) > 1:
        candidates.append(all_braces[-1].group(0).strip())

    return candidates


# ---------------------------------------------------------------------------
# Fallback: regex key-value extraction
# ---------------------------------------------------------------------------

def _regex_fallback(text: str, model_class: Type[T]) -> T | None:
    """
    Last-resort extraction: find key-value pairs using regex and
    construct a minimal dict for Pydantic validation.
    """
    fields = model_class.model_fields
    extracted: dict = {}

    for field_name, field_info in fields.items():
        # Try to find "key": value or "key": "value"
        pattern = rf'["\']?{re.escape(field_name)}["\']?\s*:\s*'

        # String values
        str_match = re.search(pattern + r'"([^"]*)"', text, re.IGNORECASE)
        if str_match:
            extracted[field_name] = str_match.group(1)
            continue

        str_match = re.search(pattern + r"'([^']*)'", text, re.IGNORECASE)
        if str_match:
            extracted[field_name] = str_match.group(1)
            continue

        # Boolean values
        bool_match = re.search(pattern + r"(true|false)", text, re.IGNORECASE)
        if bool_match:
            extracted[field_name] = bool_match.group(1).lower() == "true"
            continue

        # Numeric values
        num_match = re.search(pattern + r"([0-9]+\.?[0-9]*)", text)
        if num_match:
            val = num_match.group(1)
            extracted[field_name] = float(val) if "." in val else int(val)
            continue

    if not extracted:
        return None

    try:
        return model_class.model_validate(extracted)
    except ValidationError:
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_structured_json(text: str, model_class: Type[T]) -> T:
    """
    Parse a raw LLM text response into a validated Pydantic model instance.

    Implements a 4-layer pipeline:
      1. Extraction — multiple strategies to locate JSON
      2. Validation — Pydantic model validation
      3. Recovery — fix common JSON malformations and retry
      4. Fallback — regex key-value extraction

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

    # --- Layer 1 & 2: Extract candidates and try direct validation ---
    candidates = _extract_candidates(text)

    last_error: Exception | None = None

    for candidate in candidates:
        # Try direct parse
        try:
            data = json.loads(candidate)
            return model_class.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc

        # --- Layer 3: Recovery — apply fixes and retry ---
        recovered = candidate
        for fixer in _RECOVERY_PIPELINE:
            try:
                recovered = fixer(recovered)
            except Exception:
                continue

        if recovered != candidate:
            try:
                data = json.loads(recovered)
                return model_class.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc

    # --- Layer 4: Fallback — regex key-value extraction ---
    logger.warning(
        "All JSON extraction strategies failed for %s. Attempting regex fallback.",
        model_class.__name__,
    )
    result = _regex_fallback(text, model_class)
    if result is not None:
        logger.info("Regex fallback succeeded for %s", model_class.__name__)
        return result

    # All options exhausted
    raise JSONParsingError(
        f"Failed to extract or validate structured JSON for Pydantic model "
        f"{model_class.__name__} from LLM response. "
        f"Last error: {last_error}. "
        f"Raw response: {repr(text[:500])}"
    )
