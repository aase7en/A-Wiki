#!/usr/bin/env python3
from __future__ import annotations

"""
_extract_response.py — Response parser for delegate.sh engine wrappers.

Reads JSON response from stdin, extracts the text content, prints to stdout.
Exits with code 0 on success, 1 on error (with error type on stderr).

Usage (from shell):
    printf '%s' "$resp" | _extract_smart gemini
    printf '%s' "$resp" | _extract_smart openai
    printf '%s' "$resp" | _extract_smart anthropic

Error types (written to stderr):
    RATE_LIMIT         — 429 / 503 from provider
    AUTH_ERROR         — 401 / 403 from provider
    MODEL_NOT_FOUND    — 404 model not available
    EMPTY_RESPONSE     — response parsed but content is empty
    UNKNOWN_FORMAT     — unexpected JSON structure
    JSON_PARSE_ERROR   — invalid JSON
"""
import json
import sys


def classify_api_error(status_code: int, body_str: str) -> str | None:
    """Classify HTTP-level errors from provider responses."""
    if status_code in (429, 503):
        return "RATE_LIMIT"
    if status_code in (401, 403):
        return "AUTH_ERROR"
    if status_code == 404:
        return "MODEL_NOT_FOUND"
    if status_code >= 500:
        return "SERVER_ERROR"
    return None


def extract_gemini(data: dict) -> str:
    """Extract text from Gemini API response format."""
    candidates = data.get("candidates", [])
    if not candidates:
        # Check for block reason
        prompt_feedback = data.get("promptFeedback", {})
        block_reason = prompt_feedback.get("blockReason")
        if block_reason:
            raise ExtractionError(f"MODEL_NOT_FOUND: blocked ({block_reason})")
        raise ExtractionError("EMPTY_RESPONSE: no candidates")
    
    parts = candidates[0].get("content", {}).get("parts", [])
    if not parts:
        finish_reason = candidates[0].get("finishReason", "")
        if finish_reason in ("SAFETY", "BLOCKLIST"):
            raise ExtractionError(f"MODEL_NOT_FOUND: {finish_reason}")
        raise ExtractionError("EMPTY_RESPONSE: no parts")
    
    text = "".join(p.get("text", "") for p in parts)
    if not text.strip():
        raise ExtractionError("EMPTY_RESPONSE: empty text")
    return text.strip()


def extract_openai(data: dict) -> str:
    """Extract text from OpenAI-compatible API response format (DeepSeek, Groq, OpenRouter)."""
    choices = data.get("choices", [])
    if not choices:
        error = data.get("error", {})
        if error:
            code = error.get("code", "")
            message = error.get("message", "")
            meta = error.get("metadata", {})
            if "rate" in message.lower() or code == "rate_limit":
                raise ExtractionError(f"RATE_LIMIT: {message}")
            if code in ("insufficient_quota", "invalid_api_key", "authentication_error"):
                raise ExtractionError(f"AUTH_ERROR: {message}")
            if code == "model_not_found":
                raise ExtractionError(f"MODEL_NOT_FOUND: {message}")
            # OpenRouter-specific: check providers
            if "providers" in meta:
                provider_errors = meta.get("errors", {})
                if provider_errors:
                    first_err = list(provider_errors.values())[0] if isinstance(provider_errors, dict) else str(provider_errors)
                    raise ExtractionError(f"PROVIDER_ERROR: {first_err}")
            raise ExtractionError(f"API_ERROR: ({code}) {message}")
        raise ExtractionError("EMPTY_RESPONSE: no choices")
    
    msg = choices[0].get("message", {}) or {}
    content = msg.get("content", "") or ""
    
    # Handle reasoning content (DeepSeek R1)
    reasoning = msg.get("reasoning_content", "") or ""
    
    if not content.strip() and not reasoning.strip():
        finish_reason = choices[0].get("finish_reason", "")
        if finish_reason == "length":
            raise ExtractionError("EMPTY_RESPONSE: truncated (finish_reason=length)")
        raise ExtractionError("EMPTY_RESPONSE: empty content")
    
    result = ""
    if reasoning:
        result += f"[Reasoning]\n{reasoning.strip()}\n\n"
    result += content.strip() if content.strip() else reasoning.strip()
    return result


def extract_anthropic(data: dict) -> str:
    """Extract text from Anthropic API response format."""
    content = data.get("content", [])
    if not content:
        error = data.get("error", {})
        if error:
            err_type = error.get("type", "")
            message = error.get("message", "")
            if "rate" in message.lower() or err_type == "rate_limit_error":
                raise ExtractionError(f"RATE_LIMIT: {message}")
            if err_type == "authentication_error":
                raise ExtractionError(f"AUTH_ERROR: {message}")
            if err_type == "not_found_error":
                raise ExtractionError(f"MODEL_NOT_FOUND: {message}")
            raise ExtractionError(f"API_ERROR: ({err_type}) {message}")
        raise ExtractionError("EMPTY_RESPONSE: no content")
    
    texts = [block.get("text", "") for block in content if block.get("type") == "text"]
    result = "".join(texts).strip()
    if not result:
        raise ExtractionError("EMPTY_RESPONSE: no text blocks")
    return result


class ExtractionError(Exception):
    pass


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: _extract_response.py <format>", file=sys.stderr)
        print("  format: gemini | openai | anthropic", file=sys.stderr)
        return 1

    fmt = sys.argv[1].lower()
    raw = sys.stdin.read()
    
    if not raw.strip():
        print("EMPTY_RESPONSE: no input", file=sys.stderr)
        return 1
    
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"JSON_PARSE_ERROR: {e}", file=sys.stderr)
        return 1
    
    try:
        if fmt == "gemini":
            result = extract_gemini(data)
        elif fmt == "openai":
            result = extract_openai(data)
        elif fmt == "anthropic":
            result = extract_anthropic(data)
        else:
            print(f"UNKNOWN_FORMAT: unknown format '{fmt}'", file=sys.stderr)
            return 1
        
        print(result)
        return 0
    
    except ExtractionError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
