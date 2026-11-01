from dotenv import load_dotenv
load_dotenv()
from google.genai import types
import os
from google import genai

PRIMARY = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
FALLBACK = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash")
# USD per 1M tokens (input, output). Free tier = 0. Fill paid prices from the Gemini pricing page later.
PRICES = {PRIMARY: (0.0, 0.0), FALLBACK: (0.0, 0.0)}

USAGE = {"calls": 0, "fallbacks": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0}
_client = None


def client():
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=45000),  # 45 seconds in milliseconds
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


def ask_llm(prompt: str) -> dict:
    for model in (PRIMARY, FALLBACK):
        try:
            r = client().models.generate_content(model=model, contents=prompt)
            _record(model, r.usage_metadata)
            if model == FALLBACK:
                USAGE["fallbacks"] += 1
            return {"answer": r.text, "model": model}
        except Exception as e:
            print(f"{model} failed: {e}")
    raise RuntimeError("both models failed")