# DESIGN

WalletWatch answers audit questions on fintech annual reports and BRSRs with page citations. It masks personal data before indexing and again before answering, and treats every document as untrusted data.

## API endpoints

| Method | Path | Purpose | Week |
|---|---|---|---|
| GET | /health | Liveness check | 2 |
| POST | /llm/test | Send a prompt to the LLM; falls back to a second model if the first fails | 2 |
| GET | /usage | Calls, fallbacks, tokens and cost so far | 2 |
| POST | /ask | Answer a question with page-level citations | 3 |
| POST | /ingest | Queue a PDF for parsing, redaction and embedding | 4 |
| GET | /usage | Calls, fallbacks, tokens and cost for this server run, plus persistent totals from the usage_log table when a database is configured | 2 |
| POST | /chat | Structured JSON answer (answer, key_points, confidence) plus model, fallback_used and token counts. Retries, then falls back to a second model; returns 503 if both fail | 2 |
| POST | /chat/stream | Same prompt as /chat, plain text streamed chunk by chunk. Falls back only if the first model fails before sending text | 2 |

Every LLM call is saved to usage_log in Postgres when DATABASE_URL is set. Without a database (CI, Render for now) usage is kept in memory only.

Note: /chat and /chat/stream are general LLM endpoints, not yet grounded in the documents. /ask (Week 3) will answer from the PDFs with page citations.

## Tables (Postgres + pgvector)

| Table | Columns | Notes |
|---|---|---|
| documents | id, company, year, file, pages, sha256, source_url | One row per PDF listed in data/manifest.csv |
| chunks | id, document_id, page, text_redacted, embedding | Only redacted text is stored or embedded |
| redaction_log | id, chunk_id, type, position, reason | Never stores the original value |
| usage_log | id, ts, model, input_tokens, output_tokens, cost_usd | Feeds /usage |

## LLM calls

- Primary and fallback model names come from `.env` (`GEMINI_MODEL`, `GEMINI_FALLBACK_MODEL`).
- Each call has a timeout. If the primary model fails, the fallback is tried; if both fail, the API returns an error.
- Tokens and cost are counted per call and shown at /usage.

## Safety rules

- Retrieved document text is treated as untrusted data, never as instructions.
- Personal data (emails, phone numbers, PAN-like strings, names with contact details) is masked before indexing and again before answering.
- Raw PDFs are not stored in the repo. data/manifest.csv records the source, page count and checksum of each file.