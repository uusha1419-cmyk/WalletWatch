import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.schemas import ChatAnswer

load_dotenv()

PRIMARY = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
FALLBACK = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")
# USD per 1M tokens (input, output). Free tier = 0. Fill paid prices later.
PRICES = {PRIMARY: (0.0, 0.0), FALLBACK: (0.0, 0.0)}
TIMEOUT_MS = 20000
RETRIES = 1  # one extra try per model before moving to the fallback

SYSTEM = (
    "You are WalletWatch, an assistant for audit trainees reviewing Indian fintech "
    "companies' data-breach, KYC and fraud disclosures. Answer briefly. "
    "If you are not sure or the information is not available, say so and set "
    "confidence to low. Never invent figures. Never include personal data such as "
    "names, emails or phone numbers of individuals."
)
CHAT_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM,
    response_mime_type="application/json",
    response_schema=ChatAnswer,
)

USAGE = {
    "calls": 0,
    "fallbacks": 0,
    "retries": 0,
    "input_tokens": 0,
    "output_tokens": 0,
    "cost_usd": 0.0,
}
_client = None


def client():
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=TIMEOUT_MS),
        )
    return _client


def _record(model, meta):
    tin = getattr(meta, "prompt_token_count", 0) or 0
    tout = getattr(meta, "candidates_token_count", 0) or 0
    p_in, p_out = PRICES[model]
    USAGE["calls"] += 1
    USAGE["input_tokens"] += tin
    USAGE["output_tokens"] += tout
    USAGE["cost_usd"] += (tin * p_in + tout * p_out) / 1_000_000
    return tin, tout


def _generate(model, prompt, config):
    """Call one model; retry on failure with a short backoff."""
    last = None
    for attempt in range(RETRIES + 1):
        try:
            return client().models.generate_content(model=model, contents=prompt, config=config)
        except Exception as e:
            last = e
            print(f"{model} attempt {attempt + 1} failed: {e}")
            if attempt < RETRIES:
                USAGE["retries"] += 1
                time.sleep(1 + attempt)
    raise last


def _run(prompt, config, parse):
    """Try the primary model, then the fallback. Returns (result, model, tokens)."""
    for model in (PRIMARY, FALLBACK):
        try:
            r = _generate(model, prompt, config)
            result = parse(r)
        except Exception as e:
            print(f"{model} failed: {e}")
            continue
        tokens = _record(model, r.usage_metadata)
        if model == FALLBACK:
            USAGE["fallbacks"] += 1
        return result, model, tokens
    raise RuntimeError("both models failed")


def ask_llm(prompt: str) -> dict:
    text, model, _ = _run(prompt, None, lambda r: r.text)
    return {"answer": text, "model": model}


def _parse_answer(r):
    return r.parsed or ChatAnswer.model_validate_json(r.text)


def chat(message: str) -> dict:
    answer, model, (tin, tout) = _run(message, CHAT_CONFIG, _parse_answer)
    return {
        **answer.model_dump(),
        "model": model,
        "fallback_used": model != PRIMARY,
        "input_tokens": tin,
        "output_tokens": tout,
    }


STREAM_CONFIG = types.GenerateContentConfig(system_instruction=SYSTEM)


def chat_stream(message: str):
    """Yield text chunks. Falls back only if a model fails before sending anything."""
    for model in (PRIMARY, FALLBACK):
        started = False
        meta = None
        try:
            for chunk in client().models.generate_content_stream(
                model=model, contents=message, config=STREAM_CONFIG
            ):
                if chunk.usage_metadata:
                    meta = chunk.usage_metadata
                if chunk.text:
                    started = True
                    yield chunk.text
            _record(model, meta or object())
            if model == FALLBACK:
                USAGE["fallbacks"] += 1
            return
        except Exception as e:
            print(f"{model} stream failed: {e}")
            if started:
                yield "\n[stream interrupted]"
                return
    yield "[LLM unavailable, try again]"
