---
title: Phase 7 — Containerization Design
date: 2026-06-20
status: approved
---

## Scope

Add a production-ready `docker/Dockerfile` and wire a new `api` service into the existing `docker-compose.yml` so the FastAPI application can be built and run entirely inside Docker.

## Dockerfile — Multi-Stage Build (`docker/Dockerfile`)

Two stages, both on `python:3.11-slim`.

**Stage 1 `builder`**
- Copy `pyproject.toml`, `README.md`, and `src/` into `/app`
- Run `pip install --prefix=/install .` — installs runtime deps and the `src` package into an isolated prefix, keeping pip and hatchling build metadata out of the final image

**Stage 2 `runner`**
- Copy `/install → /usr/local` from builder (site-packages and the `uvicorn` binary land in the correct system paths automatically)
- `src` is available via site-packages; no second COPY needed
- `EXPOSE 8000`
- `CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]`

## docker-compose.yml — `api` Service

```yaml
api:
  build:
    context: .
    dockerfile: docker/Dockerfile
  ports:
    - "8000:8000"
  environment:
    GEMINI_API_KEY: ${GEMINI_API_KEY}   # host env / root .env — never hardcoded
    DB_HOST: db                          # service name (not localhost)
    DB_PORT: 5432                        # internal container port (not 5433)
    DB_USER: chatops_user
    DB_PASSWORD: chatops_password
    DB_NAME: chatops_db
  depends_on:
    db:
      condition: service_healthy         # waits for pg_isready to pass
  restart: unless-stopped
```

**Key decisions:**
- `GEMINI_API_KEY` is the only secret; it is pulled from the host shell or the root `.env` file that Docker Compose reads automatically.
- `DB_HOST=db` overrides any `.env` value so the API always reaches the correct Docker network host.
- `DB_PORT=5432` (internal) overrides the host-side `5433` mapping.
- `condition: service_healthy` leverages the existing `pg_isready` healthcheck on the `db` service.

## .dockerignore

Excludes `.venv/`, `.git/`, `tests/`, `.pytest_cache/` from the build context to prevent sending hundreds of MB of local tooling to the Docker daemon.
