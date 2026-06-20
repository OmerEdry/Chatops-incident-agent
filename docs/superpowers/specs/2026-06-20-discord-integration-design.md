---
name: discord-integration-phase8
description: Phase 8 — Discord Rich Embed alerting for P1/P2 incidents via background task
metadata:
  type: project
---

# Discord Integration — Phase 8

## Goal
Send a structured Discord Rich Embed alert to a single webhook channel for every P1_CRITICAL or P2_HIGH incident, without blocking the API response.

## Approach
Service-layer notification (`src/services/discord.py`) triggered from the route handler via FastAPI `BackgroundTasks`. No changes to the routing/LLM pipeline.

## Components

### `src/core/config.py`
- Add `DISCORD_WEBHOOK_URL: SecretStr | None = None` (optional, app starts without it).

### `src/services/discord.py`
- `send_discord_alert(incident_result: IncidentAnalysisResult) -> None`
- No-op if `DISCORD_WEBHOOK_URL` is not set.
- Embed color: `0xFF0000` (P1_CRITICAL), `0xFF8C00` (P2_HIGH).
- Embed title: `[<severity>] <summary>`.
- Embed description: `reasoning` field.
- Fields: **Root Cause** + **Recommended Actions** (bullet list) from `deep_analysis` when present.
- Footer: `"ChatOps Incident Agent"` + UTC ISO timestamp.
- All HTTP/network errors caught and logged at ERROR via `logger.exception(...)`, never re-raised.

### `src/api/routes.py`
- Inject `BackgroundTasks` into `handle_incident_webhook`.
- After result: `if result.routed_to_claude: background_tasks.add_task(send_discord_alert, result)`.

### `tests/test_api.py`
- `test_discord_alert_triggered_for_p2`: mock `route_incident` → P2 result, assert `send_discord_alert` called once.
- `test_discord_alert_not_triggered_for_p4`: mock `route_incident` → P4 result, assert `send_discord_alert` not called.
- Both tests mock `src.services.discord.send_discord_alert` with `AsyncMock`.

## Error Handling
Failures in Discord delivery are fire-and-forget. The API response is already sent before the background task runs. Errors are observable via container logs at ERROR level.

## No new dependencies
`httpx` is already in `pyproject.toml`.
