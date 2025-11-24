# Copilot instructions for contributors and AI coding agents

Purpose: help AI agents and contributors become productive quickly in this repo.

- **Entry point**: `main.py` (project runner; currently a placeholder).
- **Primary package**: `bot/` contains `config.py`, `db/`, `handlers/`, `services/`, `utils/`.

Big picture
- This repo implements a Telegram bot that searches hh.ru and generates documents via an
  OpenAI-compatible LLM (see `README.md`). Key flows:
  - User → `handlers` (aiogram) → `services` (hh_service / llm_service) → `db` → responses sent back.
  - A daily scheduler pulls filters for each user, fetches new vacancies from hh.ru,
    stores them in `db/`, and sends batches to users.

Important files & directories
- `README.md` — primary spec and functional requirements (use this as the single-source-of-truth).
- `main.py` — start/entry script (run the bot/scheduler here).
- `bot/config.py` — application configuration and environment binding (env vars like
  `TELEGRAM_TOKEN`, `DATABASE_URL`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`).
- `bot/handlers/` — aiogram handlers and conversation logic. Keep handlers thin: delegate heavy logic
  to `services`.
- `bot/services/` — business logic: `hh_service` (hh.ru API), `llm_service` (LLM API), helpers for
  document generation and vacancy selection.
- `bot/db/` — persistence layer: user profiles, filters, vacancies, generated documents, and
  user↔vacancy associations.
- `bot/utils/` — small helpers, HTTP clients, and shared utilities.

Patterns & conventions (repo-specific)
- Async-first: use `async def` throughout handlers and services; integrate with aiogram and
  async HTTP client. Keep blocking I/O out of the event loop.
- Separation of concerns: handlers only parse input and call services; services implement
  retries, deduplication, and persistence logic.
- Secrets in `.env`: never log full secrets. Logging must redact `API_KEY` and `DATABASE_URL`.
- Scheduler responsibilities: deduplicate vacancies and avoid re-sending the same vacancy to
  a user. Implement dedup checks in `bot/services` or `bot/db`.

Integration points
- hh.ru API: located conceptually in `bot/services/hh_service.py` (implement rate-limiting
  and backoff). Save raw vacancy IDs to the DB to avoid repeats.
- LLM: `bot/services/llm_service.py` or similar. Accept configurable base URL and keys to support
  different OpenAI-compatible endpoints (per README).
- Database: PostgreSQL (Neon), configured via `DATABASE_URL`.

Developer workflows
- Recommended environment (Windows PowerShell):
```
# create venv (if not present)
python -m venv .venv
; .venv\Scripts\Activate.ps1
# install deps if a requirements file is added
pip install -r requirements.txt
# run the bot (entrypoint may be empty until implemented)
python main.py
```
- If `requirements.txt` is missing, add one listing `aiogram`, `httpx[http2]` or `aiohttp`,
  `psycopg[binary]` or `asyncpg`, `apscheduler` (or similar), and any LLM SDK used.
- Tests and linters: there are no tests currently. Add `pytest` and `ruff`/`flake8` if desired.

How to make safe, useful changes
- Follow the handler → service → db flow. When adding features, create tests in a new
  `tests/` directory and prefer small commits.
- Add integration points (hh, llm) under `bot/services/` and write small adapters that accept
  configuration from `bot/config.py`.

When merging or updating this file
- If an existing `.github/copilot-instructions.md` is present, prefer the more detailed
  project-specific notes from `README.md` and keep environment / run commands accurate for
  Windows PowerShell.

Questions for maintainers
- Are there preferred HTTP clients or existing coding helpers in `bot/utils/` to reuse?
- Should scheduler be `apscheduler` or an external job runner? Indicate preferred approach.

If anything here looks incomplete or inaccurate, please point to the file(s) and I'll update
this guidance.
