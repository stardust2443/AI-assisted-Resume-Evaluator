"""
llm/client.py — Provider-agnostic LLM abstraction layer.

Current provider: Google Gemini (google-genai SDK, gemini-2.5-flash, free tier)

Resilience features:
- Automatic retry on 503 (model overload) with exponential backoff
- JSON extraction fallback if model adds preamble before JSON block
- Raises ValueError only if JSON cannot be recovered at all
"""

import json
import logging
import re
import time
from typing import Optional

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from config import settings

logger = logging.getLogger(__name__)

# Instantiate once — thread-safe
_client = genai.Client(api_key=settings.gemini_api_key)

# Retry settings for transient 503 errors
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 5  # seconds


def _repair_truncated_json(raw: str) -> str:
    """
    Attempt to repair a JSON string that was cut off mid-stream (token limit hit).
    Closes any unclosed arrays/objects so json.loads can parse it.
    Returns the repaired string (may still be invalid if truncation was severe).
    """
    # Find the start of the JSON object
    start = raw.find('{')
    if start == -1:
        return raw
    raw = raw[start:]

    # Walk through and track open structures
    stack = []
    in_string = False
    escape_next = False
    last_valid_pos = 0

    for i, ch in enumerate(raw):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            stack.append('}')
        elif ch == '[':
            stack.append(']')
        elif ch in ('}', ']'):
            if stack and stack[-1] == ch:
                stack.pop()
                last_valid_pos = i

    # Close any still-open structures in reverse order
    closing = ''.join(reversed(stack))

    # Trim to last structurally sound position and close
    truncated = raw[:last_valid_pos + 1] if stack else raw
    return truncated + closing


def _extract_json(raw: str) -> dict:
    """
    Extract a JSON object from a string that may have preamble, code fences,
    or be truncated due to token limits.

    Raises ValueError if no valid JSON can be recovered.
    """
    if not raw:
        raise ValueError("LLM returned empty response text.")

    # Attempt 1: direct parse (ideal case)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Attempt 2: strip markdown code fences
    fenced = re.sub(r'```(?:json)?\n?', '', raw).strip()
    try:
        return json.loads(fenced)
    except json.JSONDecodeError:
        pass

    # Attempt 3: extract first {...} block (handles preamble text)
    match = re.search(r'\{.*\}', fenced, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Attempt 4: repair truncated JSON (token limit mid-cut)
    try:
        repaired = _repair_truncated_json(fenced)
        return json.loads(repaired)
    except (json.JSONDecodeError, Exception):
        pass

    raise ValueError(
        f"Could not extract valid JSON from LLM response.\nRaw (first 300 chars): {raw[:300]}"
    )


def complete_json(
    system: str,
    user: str,
    max_tokens: int,
    temperature: Optional[float] = None,
) -> dict:
    """
    Send a system + user prompt to Gemini and return the parsed JSON response.

    Args:
        system:      System instruction (sets model behavior/persona)
        user:        User-turn content (the actual task)
        max_tokens:  Max output tokens
        temperature: Override; defaults to settings.llm.temperature

    Returns:
        dict: Parsed JSON from model response

    Raises:
        ValueError: If model returns non-JSON output after all recovery attempts
        Exception:  Re-raises non-retryable API errors
    """
    temp = temperature if temperature is not None else settings.llm.temperature
    full_prompt = f"{system}\n\n{user}"

    logger.debug(
        "LLM call → model=%s, max_tokens=%d, temp=%s",
        settings.llm.model, max_tokens, temp,
    )

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            response = _client.models.generate_content(
                model=settings.llm.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=temp,
                    max_output_tokens=max_tokens,
                ),
            )

            raw = response.text
            result = _extract_json(raw)
            if attempt > 1:
                logger.info("LLM call succeeded on attempt %d", attempt)
            return result

        except (genai_errors.ServerError, genai_errors.APIError) as e:
            status = getattr(e, 'status_code', None) or getattr(e, 'code', None)
            # Retry only on 503 (model overload) or 529 (overloaded)
            if status in (503, 529) and attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))  # 5s, 10s, 20s
                logger.warning(
                    "Gemini %s on attempt %d/%d. Retrying in %ds...",
                    status, attempt, _MAX_RETRIES, delay,
                )
                time.sleep(delay)
                last_error = e
                continue
            raise  # Non-retryable: 400, 401, 404, 429 — bubble up immediately

        except ValueError as e:
            # JSON extraction failed — not retryable
            logger.error("JSON extraction failed: %s", e)
            raise

    # All retries exhausted
    raise last_error
