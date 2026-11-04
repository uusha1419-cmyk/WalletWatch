import os

import psycopg

_ready = False

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS usage_log (
    id BIGSERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL DEFAULT now(),
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    cost_usd NUMERIC(12, 6) NOT NULL
)
"""


def _connect():
    url = os.getenv("DATABASE_URL")
    return psycopg.connect(url, connect_timeout=3) if url else None


def log_usage(model: str, tokens_in: int, tokens_out: int, cost: float) -> None:
    """Save one LLM call. Never raises: logging must not break an answer."""
    global _ready
    try:
        conn = _connect()
        if conn is None:
            return
        with conn:
            if not _ready:
                conn.execute(CREATE_SQL)
                _ready = True
            conn.execute(
                "INSERT INTO usage_log (model, input_tokens, output_tokens, cost_usd)"
                " VALUES (%s, %s, %s, %s)",
                (model, tokens_in, tokens_out, cost),
            )
    except Exception as e:
        print(f"usage_log failed: {e}")


def totals() -> dict | None:
    """Totals across all saved calls, or None if there is no database."""
    try:
        conn = _connect()
        if conn is None:
            return None
        with conn:
            conn.execute(CREATE_SQL)
            calls, tin, tout, cost = conn.execute(
                "SELECT count(*), coalesce(sum(input_tokens), 0),"
                " coalesce(sum(output_tokens), 0), coalesce(sum(cost_usd), 0)"
                " FROM usage_log"
            ).fetchone()
        return {
            "calls": calls,
            "input_tokens": int(tin),
            "output_tokens": int(tout),
            "cost_usd": float(cost),
        }
    except Exception as e:
        print(f"usage totals failed: {e}")
        return None
