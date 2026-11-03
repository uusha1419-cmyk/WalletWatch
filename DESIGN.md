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