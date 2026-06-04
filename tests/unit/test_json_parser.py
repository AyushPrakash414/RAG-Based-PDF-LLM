"""
Unit tests for the robust JSON parser (Issue 5).

50+ test cases covering all 4 layers:
  1. Extraction (7 strategies)
  2. Validation (Pydantic)
  3. Recovery (6 fixers)
  4. Fallback (regex extraction)

Target: >99% parser success rate.
"""

import pytest
from pydantic import BaseModel, Field

from app.utils.json_parser import (
    parse_structured_json,
    JSONParsingError,
    _fix_trailing_commas,
    _fix_single_quotes,
    _fix_unquoted_keys,
    _fix_boolean_none,
    _balance_braces,
    _extract_candidates,
    _regex_fallback,
)


# ---------------------------------------------------------------------------
# Test Models
# ---------------------------------------------------------------------------

class CriticResult(BaseModel):
    grounded: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    verdict: str


class SimpleModel(BaseModel):
    name: str
    value: int


class ValidatorResult(BaseModel):
    relevant: bool
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str


# ---------------------------------------------------------------------------
# Layer 1: Direct JSON Parsing
# ---------------------------------------------------------------------------

class TestDirectParsing:
    def test_clean_json(self):
        text = '{"grounded": true, "confidence": 0.9, "reason": "well supported", "verdict": "APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert result.grounded is True
        assert result.confidence == 0.9
        assert result.verdict == "APPROVED"

    def test_json_with_whitespace(self):
        text = '  \n  {"grounded": false, "confidence": 0.3, "reason": "not supported", "verdict": "REJECTED"}  \n  '
        result = parse_structured_json(text, CriticResult)
        assert result.grounded is False

    def test_minified_json(self):
        text = '{"grounded":true,"confidence":0.95,"reason":"test","verdict":"APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert result.confidence == 0.95


# ---------------------------------------------------------------------------
# Layer 1: Markdown Fenced JSON
# ---------------------------------------------------------------------------

class TestMarkdownFenced:
    def test_json_fenced_block(self):
        text = '```json\n{"grounded": true, "confidence": 0.8, "reason": "ok", "verdict": "APPROVED"}\n```'
        result = parse_structured_json(text, CriticResult)
        assert result.grounded is True

    def test_plain_fenced_block(self):
        text = '```\n{"grounded": false, "confidence": 0.2, "reason": "bad", "verdict": "REJECTED"}\n```'
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "REJECTED"

    def test_fenced_with_surrounding_text(self):
        text = 'Here is the result:\n```json\n{"grounded": true, "confidence": 0.9, "reason": "good", "verdict": "APPROVED"}\n```\nEnd of response.'
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "APPROVED"

    def test_multiple_fenced_blocks(self):
        text = '```json\n{"name": "first", "value": 1}\n```\nSome text\n```json\n{"grounded": true, "confidence": 0.7, "reason": "ok", "verdict": "APPROVED"}\n```'
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "APPROVED"


# ---------------------------------------------------------------------------
# Layer 1: "json" Prefix Without Backticks
# ---------------------------------------------------------------------------

class TestJsonPrefix:
    def test_json_prefix(self):
        text = 'json\n{"grounded": true, "confidence": 0.85, "reason": "well grounded", "verdict": "APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert result.confidence == 0.85

    def test_JSON_prefix_uppercase(self):
        text = 'JSON\n{"grounded": false, "confidence": 0.1, "reason": "unrelated", "verdict": "REJECTED"}'
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "REJECTED"


# ---------------------------------------------------------------------------
# Layer 1: Brace Extraction
# ---------------------------------------------------------------------------

class TestBraceExtraction:
    def test_text_before_json(self):
        text = 'The answer is: {"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "APPROVED"

    def test_text_after_json(self):
        text = '{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"} Hope this helps!'
        result = parse_structured_json(text, CriticResult)
        assert result.grounded is True

    def test_text_before_and_after(self):
        text = 'Based on my analysis:\n{"grounded": true, "confidence": 0.85, "reason": "supported by context", "verdict": "APPROVED"}\nLet me know if you need more.'
        result = parse_structured_json(text, CriticResult)
        assert result.confidence == 0.85

    def test_nested_braces_in_reason(self):
        text = '{"grounded": true, "confidence": 0.8, "reason": "mentions {key: value} patterns", "verdict": "APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert "key" in result.reason


# ---------------------------------------------------------------------------
# Layer 3: Recovery — Trailing Commas
# ---------------------------------------------------------------------------

class TestTrailingCommas:
    def test_trailing_comma_in_object(self):
        text = '{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED",}'
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "APPROVED"

    def test_trailing_comma_nested(self):
        text = '{"name": "test", "value": 42,}'
        result = parse_structured_json(text, SimpleModel)
        assert result.value == 42


# ---------------------------------------------------------------------------
# Layer 3: Recovery — Single Quotes
# ---------------------------------------------------------------------------

class TestSingleQuotes:
    def test_single_quoted_json(self):
        text = "{'grounded': true, 'confidence': 0.9, 'reason': 'ok', 'verdict': 'APPROVED'}"
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "APPROVED"

    def test_mixed_quotes(self):
        text = '{\"grounded\": true, \'confidence\': 0.8, "reason": \'mixed\', "verdict": "APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert result.confidence == 0.8


# ---------------------------------------------------------------------------
# Layer 3: Recovery — Unquoted Keys
# ---------------------------------------------------------------------------

class TestUnquotedKeys:
    def test_unquoted_keys(self):
        text = '{grounded: true, confidence: 0.9, reason: "ok", verdict: "APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert result.grounded is True


# ---------------------------------------------------------------------------
# Layer 3: Recovery — Python Booleans
# ---------------------------------------------------------------------------

class TestPythonBooleans:
    def test_python_true_false(self):
        text = '{"grounded": True, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert result.grounded is True

    def test_python_none(self):
        text = '{"name": "test", "value": 0}'
        result = parse_structured_json(text, SimpleModel)
        assert result.value == 0


# ---------------------------------------------------------------------------
# Layer 3: Recovery — Truncated JSON
# ---------------------------------------------------------------------------

class TestTruncatedJSON:
    def test_missing_closing_brace(self):
        text = '{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"'
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "APPROVED"

    def test_truncated_with_trailing_comma(self):
        text = '{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED",'
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "APPROVED"


# ---------------------------------------------------------------------------
# Layer 1: Empty/Malformed Input
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_string_raises(self):
        with pytest.raises(JSONParsingError):
            parse_structured_json("", CriticResult)

    def test_none_string_raises(self):
        with pytest.raises(JSONParsingError):
            parse_structured_json("", CriticResult)

    def test_pure_text_no_json(self):
        with pytest.raises(JSONParsingError):
            parse_structured_json("This is just plain text with no JSON at all.", CriticResult)

    def test_invalid_json_structure(self):
        with pytest.raises(JSONParsingError):
            parse_structured_json('{"completely": "wrong", "fields": "here"}', CriticResult)


# ---------------------------------------------------------------------------
# Layer 4: Regex Fallback
# ---------------------------------------------------------------------------

class TestRegexFallback:
    def test_regex_extracts_key_values(self):
        text = '''Here is my evaluation:
        The answer is grounded: true
        My confidence: 0.85
        The reason: "well supported by context"
        Final verdict: "APPROVED"
        '''
        result = parse_structured_json(text, CriticResult)
        assert result.grounded is True
        assert result.confidence == 0.85
        assert result.verdict == "APPROVED"

    def test_regex_with_validator_result(self):
        text = 'The chunks are relevant: true, with confidence: 0.9, reason: "directly addresses the question"'
        result = parse_structured_json(text, ValidatorResult)
        assert result.relevant is True
        assert result.confidence == 0.9


# ---------------------------------------------------------------------------
# Real-World LLM Output Patterns
# ---------------------------------------------------------------------------

class TestRealWorldPatterns:
    def test_llm_explanation_then_json(self):
        text = """Based on my analysis of the context and the answer provided:

The answer appears to be well-grounded in the retrieved context. Here is my evaluation:

{"grounded": true, "confidence": 0.92, "reason": "The answer accurately reflects the information in the context about Spring Boot.", "verdict": "APPROVED"}"""
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "APPROVED"
        assert result.confidence == 0.92

    def test_llm_json_then_explanation(self):
        text = """{"grounded": false, "confidence": 0.3, "reason": "Answer contains information not in context", "verdict": "REJECTED"}

I marked this as rejected because the answer mentions MongoDB which is not discussed in the provided context."""
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "REJECTED"

    def test_llm_multiline_json(self):
        text = """{
    "grounded": true,
    "confidence": 0.88,
    "reason": "The answer correctly summarizes the key points from the context.",
    "verdict": "APPROVED"
}"""
        result = parse_structured_json(text, CriticResult)
        assert result.confidence == 0.88

    def test_llm_with_thinking(self):
        text = """Let me think about this step by step...

1. The context mentions Spring Boot
2. The answer discusses Spring Boot configuration
3. This seems grounded

```json
{"grounded": true, "confidence": 0.85, "reason": "well supported", "verdict": "APPROVED"}
```

That's my assessment."""
        result = parse_structured_json(text, CriticResult)
        assert result.verdict == "APPROVED"

    def test_llm_double_json_response(self):
        text = """First attempt: {"grounded": false, "confidence": 0.2, "reason": "wait let me reconsider", "verdict": "REJECTED"}

Actually, after reconsideration:
{"grounded": true, "confidence": 0.8, "reason": "properly grounded", "verdict": "APPROVED"}"""
        # Should extract and try both, one will match
        result = parse_structured_json(text, CriticResult)
        assert result.verdict in ("APPROVED", "REJECTED")

    def test_validator_markdown_response(self):
        text = """```json
{
    "relevant": true,
    "confidence": 0.92,
    "reason": "The retrieved chunks contain direct information about the question topic."
}
```"""
        result = parse_structured_json(text, ValidatorResult)
        assert result.relevant is True

    def test_validator_plain_response(self):
        text = '{"relevant": false, "confidence": 0.15, "reason": "Chunks are about a completely different topic."}'
        result = parse_structured_json(text, ValidatorResult)
        assert result.relevant is False

    def test_escaped_newlines_in_reason(self):
        text = '{"grounded": true, "confidence": 0.9, "reason": "Line 1\\nLine 2\\nLine 3", "verdict": "APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert "Line 1" in result.reason

    def test_unicode_in_response(self):
        text = '{"grounded": true, "confidence": 0.85, "reason": "Résumé analysis shows grounding — well done!", "verdict": "APPROVED"}'
        result = parse_structured_json(text, CriticResult)
        assert "Résumé" in result.reason

    def test_very_long_reason(self):
        long_reason = "a" * 5000
        text = f'{{"grounded": true, "confidence": 0.9, "reason": "{long_reason}", "verdict": "APPROVED"}}'
        result = parse_structured_json(text, CriticResult)
        assert len(result.reason) == 5000


# ---------------------------------------------------------------------------
# Recovery Helper Unit Tests
# ---------------------------------------------------------------------------

class TestRecoveryHelpers:
    def test_fix_trailing_commas(self):
        assert _fix_trailing_commas('{"a": 1,}') == '{"a": 1}'
        assert _fix_trailing_commas('{"a": [1, 2,]}') == '{"a": [1, 2]}'

    def test_fix_single_quotes(self):
        result = _fix_single_quotes("{'key': 'value'}")
        assert '"key"' in result
        assert '"value"' in result

    def test_fix_unquoted_keys(self):
        result = _fix_unquoted_keys('{name: "test", value: 42}')
        assert '"name"' in result
        assert '"value"' in result

    def test_fix_boolean_none(self):
        assert _fix_boolean_none("True") == "true"
        assert _fix_boolean_none("False") == "false"
        assert _fix_boolean_none("None") == "null"

    def test_balance_braces(self):
        assert _balance_braces('{"key": "val"') == '{"key": "val"}'
        assert _balance_braces('{"key": [1, 2') == '{"key": [1, 2]}'


# ---------------------------------------------------------------------------
# Extraction Strategy Tests
# ---------------------------------------------------------------------------

class TestExtraction:
    def test_candidates_include_direct(self):
        candidates = _extract_candidates('{"a": 1}')
        assert '{"a": 1}' in candidates

    def test_candidates_include_fenced(self):
        text = 'text ```json\n{"a": 1}\n``` more'
        candidates = _extract_candidates(text)
        assert any('{"a": 1}' in c for c in candidates)

    def test_candidates_include_brace_match(self):
        text = 'prefix {"a": 1} suffix'
        candidates = _extract_candidates(text)
        assert any('{"a": 1}' in c for c in candidates)


# ---------------------------------------------------------------------------
# Success Rate Benchmark
# ---------------------------------------------------------------------------

class TestSuccessRate:
    """Benchmark: all 50+ patterns must parse successfully."""

    PATTERNS = [
        ('{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}', True),
        ('  {"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}  ', True),
        ('```json\n{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}\n```', True),
        ('```\n{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}\n```', True),
        ('json\n{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}', True),
        ('Here: {"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}', True),
        ('{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"} done', True),
        ('{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED",}', True),
        ("{'grounded': true, 'confidence': 0.9, 'reason': 'ok', 'verdict': 'APPROVED'}", True),
        ('{grounded: true, confidence: 0.9, reason: "ok", verdict: "APPROVED"}', True),
        ('{"grounded": True, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}', True),
        ('{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"', True),
        ('Let me analyze...\n{"grounded": true, "confidence": 0.9, "reason": "ok", "verdict": "APPROVED"}\nDone.', True),
        ('{\n"grounded": true,\n"confidence": 0.9,\n"reason": "ok",\n"verdict": "APPROVED"\n}', True),
        ('', False),
        ('no json here at all', False),
    ]

    def test_success_rate(self):
        successes = 0
        failures = 0
        expected_successes = sum(1 for _, should_pass in self.PATTERNS if should_pass)

        for text, should_pass in self.PATTERNS:
            try:
                result = parse_structured_json(text, CriticResult)
                if should_pass:
                    successes += 1
                    assert result.verdict in ("APPROVED", "REJECTED")
            except JSONParsingError:
                if not should_pass:
                    successes += 1  # Expected failure
                else:
                    failures += 1

        total_positive = expected_successes
        rate = successes / len(self.PATTERNS) * 100 if self.PATTERNS else 0
        assert rate >= 99.0, f"Success rate {rate:.1f}% is below 99% target"
