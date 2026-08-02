# Phase B — Production Infrastructure Implementation Plan

## Overview

Transform the Fundfy backend from a local dev prototype (SQLite, in-memory dicts, no auth) to production-ready infrastructure (PostgreSQL, Redis, background workers, auth, Docker, CI/CD).

---

## Implementation Plan

- [ ] 1. **Update environment configuration and add new dependencies**
      Add all Phase B dependencies to `pyproject.toml` (asyncpg, redis, arq, alembic, pyjwt, structlog, python-multipart, passlib, bcrypt) and create an environment-based config system in `fundfy/config.py` that supports development/staging/production modes, PostgreSQL URL, Redis URL, JWT secrets, ChromaDB server URL, and worker settings. Update `.env.example` with all new variables.
      Files: `pyproject.toml`, `fundfy/config.py`, `.env.example`, `.env`
      Verify: `cd /projects/sandbox/Fundfy && pip install -e ".[dev]"` completes successfully; `python -c "from fundfy.config import settings; print(settings.database_url)"` prints the configured URL.

- [ ] 2. **Restructure SQLAlchemy for PostgreSQL and add new models for in-memory stores**
      Modify `fundfy/db.py` to use asyncpg connection pooling (`pool_size=20`, `max_overflow=10`) when `DATABASE_URL` starts with `postgresql`, and fall back to aiosqlite for testing. Add `password_hash` and `role` columns to the `Founder` model for auth. Add a new `EmailDraft` model in `fundfy/models/email_draft.py` and a `GeneratedFile` model in `fundfy/models/generated_file.py` to replace the in-memory `_email_drafts` list and the filesystem-only file tracking. Add a `BackgroundJob` model in `fundfy/models/job.py` for tracking job status. Update `fundfy/models/__init__.py` to export all new models.
      Files: `fundfy/db.py`, `fundfy/models/__init__.py`, `fundfy/models/founder.py`, `fundfy/models/email_draft.py`, `fundfy/models/generated_file.py`, `fundfy/models/job.py`
      Verify: `python -c "from fundfy.models import Base, EmailDraft, GeneratedFile; print('OK')"` succeeds.

- [ ] 3. **Set up Alembic for schema migrations**
      Initialize Alembic in the project root, configure `alembic.ini` and `alembic/env.py` to use the async SQLAlchemy engine from `fundfy.db` and import all models from `fundfy.models`. Generate the initial migration that creates all tables (founders, businesses, conversations, messages, documents, workstream_tasks, email_drafts, generated_files, background_jobs). Remove the `init_db()` function's `create_all` call (keep the function for backward compat during tests but have it no-op in production when Alembic manages schema).
      Files: `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/001_initial_schema.py`, `fundfy/db.py`
      Verify: `cd /projects/sandbox/Fundfy && alembic check` shows no pending ops (or `alembic heads` prints the revision).

- [ ] 4. **Migrate in-memory stores to database in route handlers**
      Rewrite `routes_business.py` to use SQLAlchemy session (via `get_session` dependency) instead of the `_businesses` dict — INSERT on create, SELECT on get. Similarly rewrite `routes_documents.py` (store to `documents` table), `routes_execution.py` (store to `workstream_tasks` table), and `routes_communication.py` (persist session state to a new `communication_sessions` table or keep in-memory for now since it holds live LLM state — decision: keep communication sessions in-memory since they hold live LLM chain state and are ephemeral). Update `routes_files.py` to also record file metadata in the `generated_files` table. Update the `email_tool.py` to persist drafts to the `email_drafts` table via a passed-in session or a direct engine usage (pass db session factory through tool initialization).
      Files: `fundfy/api/routes_business.py`, `fundfy/api/routes_documents.py`, `fundfy/api/routes_execution.py`, `fundfy/api/routes_files.py`, `fundfy/tools/email_tool.py`, `fundfy/tools/registry.py`
      Verify: `cd /projects/sandbox/Fundfy && python -m pytest tests/test_api.py tests/test_integration.py -x` — tests pass (update fixtures to use async sqlite for tests).

- [ ] 5. **Set up Redis client module**
      Create `fundfy/redis.py` that initializes an async Redis client (using `redis.asyncio`) with connection pooling, provides `get_redis()` dependency, and exposes helper functions: `cache_set(key, value, ttl)`, `cache_get(key)`, `cache_delete(key)`. Add a startup/shutdown hook in `main.py` lifespan to open and close the Redis pool. When `REDIS_URL` is empty (e.g., in tests), provide a no-op stub that returns None for all gets.
      Files: `fundfy/redis.py`, `fundfy/main.py`
      Verify: `python -c "from fundfy.redis import get_redis; print('OK')"` succeeds.

- [ ] 6. **Add structured logging with structlog**
      Create `fundfy/logging.py` that configures structlog with JSON output (for production) or colored console output (for development), based on the `ENVIRONMENT` setting. Add a request-ID middleware in `fundfy/middleware/request_id.py` that generates a UUID for each request, binds it to structlog context, and adds it to response headers (`X-Request-ID`). Add a request/response logging middleware that logs method, path, status code, and duration. Wire both middlewares into `main.py`.
      Files: `fundfy/logging.py`, `fundfy/middleware/__init__.py`, `fundfy/middleware/request_id.py`, `fundfy/middleware/logging.py`, `fundfy/main.py`
      Verify: `python -c "from fundfy.logging import setup_logging; setup_logging(); print('OK')"` succeeds; starting the app logs structured output.

- [ ] 7. **Add rate limiting middleware**
      Create `fundfy/middleware/rate_limit.py` with a Redis-based sliding-window rate limiter. Implement as FastAPI middleware that checks `Authorization` header (or IP for unauthenticated) and applies per-route limits: `/api/chat` → 60/min, `/api/documents/generate` → 10/min, `/api/execute` → 5/min, all others → 120/min. Return 429 with `Retry-After` header when exceeded. When Redis is unavailable, skip rate limiting (fail-open for availability). Register in `main.py`.
      Files: `fundfy/middleware/rate_limit.py`, `fundfy/main.py`
      Verify: `python -c "from fundfy.middleware.rate_limit import RateLimitMiddleware; print('OK')"` succeeds.

- [ ] 8. **Add ARQ background worker infrastructure**
      Create `fundfy/worker/__init__.py` and `fundfy/worker/tasks.py` that defines ARQ task functions for long-running operations: `task_execute_plan(ctx, business_id, objective, context)`, `task_generate_document(ctx, business_id, doc_type, context)`, `task_react_agent_run(ctx, founder_id, objective)`. Create `fundfy/worker/settings.py` with the ARQ `WorkerSettings` class (redis connection, job timeout=300s, max retries=3, retry delay with exponential backoff). Create a `BackgroundJobManager` in `fundfy/worker/manager.py` that enqueues jobs, stores job IDs in the `background_jobs` table, and provides status lookup. Add a `/api/jobs/{job_id}` polling endpoint in a new `fundfy/api/routes_jobs.py`.
      Files: `fundfy/worker/__init__.py`, `fundfy/worker/tasks.py`, `fundfy/worker/settings.py`, `fundfy/worker/manager.py`, `fundfy/api/routes_jobs.py`, `fundfy/main.py`
      Verify: `python -c "from fundfy.worker.settings import WorkerSettings; print(WorkerSettings)"` succeeds; `python -c "from fundfy.api.routes_jobs import router; print(router.routes)"` shows the job status route.

- [ ] 9. **Integrate background workers into API routes**
      Modify `routes_execution.py` to enqueue `task_execute_plan` via the `BackgroundJobManager` instead of running synchronously — return immediately with `{"job_id": ..., "status": "queued"}`. Modify `routes_documents.py`'s generate endpoint to enqueue `task_generate_document` for production (keep synchronous path available when `BACKGROUND_JOBS_ENABLED=false` for testing). Update `routes_chat.py` so that when the ReAct agent is invoked and the classification is `TOOL_USE`, it optionally dispatches to a background job if the estimated complexity is high (decision: for now, chat remains synchronous since users expect immediate responses, but execution and document generation go async). Update response schemas to include optional `job_id` field.
      Files: `fundfy/api/routes_execution.py`, `fundfy/api/routes_documents.py`, `fundfy/api/schemas.py`, `fundfy/worker/tasks.py`
      Verify: `cd /projects/sandbox/Fundfy && python -m pytest tests/test_api.py -x` passes (with background jobs disabled in test config).

- [ ] 10. **Add JWT authentication backend**
       Create `fundfy/auth/__init__.py` and `fundfy/auth/jwt.py` with functions: `create_access_token(founder_id, role, expires_delta)`, `decode_access_token(token) -> TokenPayload`, and a `verify_token` FastAPI dependency that extracts the token from `Authorization: Bearer <token>` header, validates it (using PyJWT with HS256 and the `JWT_SECRET` from config), and returns the `TokenPayload` (containing `founder_id` and `role`). Create `fundfy/auth/middleware.py` with a middleware that skips `/health`, `/ready`, and `/api/auth/*` routes but requires valid JWT on all other `/api/` routes. Add auth routes in `fundfy/api/routes_auth.py`: `POST /api/auth/register` (creates founder with hashed password), `POST /api/auth/login` (validates credentials, returns JWT), `POST /api/auth/refresh` (refreshes token). Use passlib/bcrypt for password hashing.
       Files: `fundfy/auth/__init__.py`, `fundfy/auth/jwt.py`, `fundfy/auth/middleware.py`, `fundfy/api/routes_auth.py`, `fundfy/main.py`
       Verify: `python -c "from fundfy.auth.jwt import create_access_token, decode_access_token; t = create_access_token('f1', 'founder'); p = decode_access_token(t); assert p.founder_id == 'f1'"` succeeds.

- [ ] 11. **Wire authentication into existing routes**
       Add the `verify_token` dependency to all route handlers (chat, business, execution, documents, communication, files, jobs). Replace client-provided `founder_id` in request bodies with the `founder_id` extracted from the JWT token payload. Update `ChatRequest` and other schemas to remove `founder_id` field (it comes from the token now). Update existing test fixtures to include a valid JWT token header (create a `conftest.py` helper `auth_headers(founder_id)` that generates a test token).
       Files: `fundfy/api/routes_chat.py`, `fundfy/api/routes_business.py`, `fundfy/api/routes_execution.py`, `fundfy/api/routes_documents.py`, `fundfy/api/routes_communication.py`, `fundfy/api/routes_files.py`, `fundfy/api/routes_jobs.py`, `fundfy/api/schemas.py`, `tests/conftest.py`
       Verify: `cd /projects/sandbox/Fundfy && python -m pytest tests/ -x` — all tests pass with auth headers.

- [ ] 12. **Add NextAuth.js to the frontend**
       Install `next-auth@5` (NextAuth v5) in the frontend. Create `frontend/auth.ts` with NextAuth configuration using CredentialsProvider (email/password hitting backend `/api/auth/login`) and GoogleProvider (with env vars `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`). Create `frontend/app/api/auth/[...nextauth]/route.ts` for the NextAuth API route. Create `frontend/middleware.ts` to protect all routes except `/` and `/api/auth`. Update `frontend/lib/api.ts` to include the session token in all requests via an `Authorization: Bearer` header (retrieve from NextAuth session). Create a login page at `frontend/app/login/page.tsx`. Update `frontend/lib/workspace-context.tsx` to get `founderId` from the NextAuth session instead of localStorage.
       Files: `frontend/auth.ts`, `frontend/app/api/auth/[...nextauth]/route.ts`, `frontend/middleware.ts`, `frontend/lib/api.ts`, `frontend/app/login/page.tsx`, `frontend/lib/workspace-context.tsx`, `frontend/package.json`
       Verify: `cd /projects/sandbox/Fundfy/frontend && npm install && npm run build` completes without errors.

- [ ] 13. **Add enhanced health check and readiness endpoints**
       Expand the `/health` endpoint to check PostgreSQL (execute `SELECT 1`), Redis (execute `PING`), ChromaDB (heartbeat via HTTP to chromadb server URL), and report each component's status. Add a `/ready` endpoint that returns 200 only when all dependencies are healthy, or 503 otherwise. Keep backward compatibility: `/health` always returns 200 with component statuses listed (for monitoring), `/ready` returns 503 if any component is down (for orchestrator probes).
       Files: `fundfy/api/routes_health.py`, `fundfy/main.py`
       Verify: `cd /projects/sandbox/Fundfy && python -m pytest tests/test_health.py -x` passes (mock Redis/PG in tests).

- [ ] 14. **Create Docker infrastructure**
       Create `Dockerfile` for the backend (Python 3.11-slim, install deps, copy code, run uvicorn). Create `frontend/Dockerfile` for the frontend (Node 22-alpine, install deps, build, run next start). Create `docker-compose.yml` with services: `backend` (FastAPI on port 8000), `frontend` (Next.js on port 3000), `postgres` (PostgreSQL 16, volume-mounted data, healthcheck), `redis` (Redis 7, healthcheck), `worker` (same image as backend, runs `arq fundfy.worker.settings.WorkerSettings`), `chromadb` (chromadb/chroma:latest, volume-mounted, healthcheck). Add `.dockerignore` for both backend and frontend. Configure environment variables via `docker-compose.yml` env section and `.env` file. Add `depends_on` with health check conditions so services start in order.
       Files: `Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, `.dockerignore`, `frontend/.dockerignore`
       Verify: `cd /projects/sandbox/Fundfy && docker compose config` validates without errors (syntax check only; full `docker compose up` requires Docker daemon).

- [ ] 15. **Create GitHub Actions CI/CD pipeline**
       Create `.github/workflows/ci.yml` with jobs: (1) `lint` — runs `ruff check fundfy/ tests/` and `ruff format --check fundfy/ tests/`; (2) `test` — uses PostgreSQL 16 and Redis 7 service containers, runs `alembic upgrade head` then `pytest --tb=short`; (3) `frontend` — runs `npm ci && npm run lint && npm run build` in the frontend directory; (4) `docker-build` — builds both Docker images (no push, just verify they build). Add `ruff` to dev dependencies in `pyproject.toml`. Create `ruff.toml` with basic config (line-length=120, target Python 3.11).
       Files: `.github/workflows/ci.yml`, `ruff.toml`, `pyproject.toml`
       Verify: File `.github/workflows/ci.yml` is valid YAML; `cd /projects/sandbox/Fundfy && pip install ruff && ruff check fundfy/ --select E,F --ignore E501` runs without crashing.

- [ ] 16. **Update tests for new infrastructure**
       Create `tests/conftest.py` with shared fixtures: async PostgreSQL test engine (using SQLite in-memory for unit tests since CI may not have PG available for all test types), Redis mock (use `fakeredis` package), auth token helper. Update `tests/test_db.py` to test with the new models (EmailDraft, GeneratedFile, BackgroundJob). Add `tests/test_auth.py` testing registration, login, token validation, and protected route access. Add `tests/test_worker.py` with unit tests for the job manager (mock ARQ pool). Update `tests/test_api.py` and `tests/test_integration.py` to include auth headers and work with database-backed routes. Add `fakeredis` to dev dependencies.
       Files: `tests/conftest.py`, `tests/test_auth.py`, `tests/test_worker.py`, `tests/test_db.py`, `tests/test_api.py`, `tests/test_integration.py`, `pyproject.toml`
       Verify: `cd /projects/sandbox/Fundfy && python -m pytest tests/ -x --tb=short` — all tests pass.

- [ ] 17. **Final integration: update main.py lifespan and dependency wiring**
       Consolidate `main.py` lifespan to: (1) set up logging, (2) run Alembic migrations (only in dev mode; production assumes pre-applied), (3) initialize Redis pool, (4) initialize DB engine with pool, (5) initialize ChromaDB with server URL if configured, (6) create all service instances and call `init_dependencies`, (7) on shutdown close Redis and DB pools. Ensure middleware ordering is correct: RequestID → Logging → RateLimit → Auth → CORS. Verify that when `ENVIRONMENT=test`, the app skips Redis/PG and uses SQLite + no-op Redis stub (for the existing test pattern).
       Files: `fundfy/main.py`, `fundfy/dependencies.py`
       Verify: `cd /projects/sandbox/Fundfy && python -m pytest tests/ --tb=short` — full test suite passes; `python -c "from fundfy.main import app; print(app.title)"` prints the app title.

---

## Dependency Order Summary

```
Step 1 (config/deps) → Step 2 (models) → Step 3 (alembic) → Step 4 (route migration)
Step 1 → Step 5 (redis) → Step 7 (rate limit)
Step 2 + Step 5 → Step 8 (worker infra) → Step 9 (worker integration)
Step 1 → Step 6 (logging)
Step 2 → Step 10 (auth backend) → Step 11 (auth wiring) → Step 12 (frontend auth)
Step 5 + Step 4 → Step 13 (health checks)
Steps 1-13 → Step 14 (docker)
Steps 1-14 → Step 15 (CI/CD)
Steps 1-14 → Step 16 (tests)
Steps 1-16 → Step 17 (final integration)
```

## Key Design Decisions

1. **ARQ over Celery**: ARQ is async-native, lightweight, and avoids the complexity of Celery's broker setup. It uses Redis directly which we already have.
2. **Chat stays synchronous**: Users expect immediate chat responses. Only execution plans and document generation are dispatched to background workers.
3. **Communication sessions stay in-memory**: They hold live LLM chain state that cannot be serialized to DB. They're ephemeral by nature.
4. **SQLite for test fixtures**: Unit tests use SQLite in-memory for speed and zero-dependency testing. Integration tests in CI use PostgreSQL service containers.
5. **Fail-open rate limiting**: If Redis is down, requests pass through rather than blocking all API traffic.
6. **Auth middleware (not per-route decorator)**: Centralized middleware means new routes are automatically protected; only explicit exemptions (health, auth endpoints) bypass it.
7. **NextAuth v5 with Credentials + Google**: Provides immediate email/password auth and easy OAuth extension. Backend validates JWT regardless of how the frontend obtained it.
8. **Alembic auto-migration in dev only**: Production deployments should run `alembic upgrade head` as a pre-deploy step, not at app startup.
