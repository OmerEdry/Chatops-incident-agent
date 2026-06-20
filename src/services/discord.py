# src/services/discord.py
import logging
from datetime import datetime, timezone

import httpx

from src.core.config import get_settings
from src.db.models import IncidentSeverity
from src.services.schemas import IncidentAnalysisResult

logger = logging.getLogger(__name__)

_SEVERITY_COLOR: dict[IncidentSeverity, int] = {
    IncidentSeverity.P1_CRITICAL: 0xFF0000,
    IncidentSeverity.P2_HIGH: 0xFF8C00,
}


async def send_discord_alert(incident_result: IncidentAnalysisResult) -> None:
    settings = get_settings()
    if settings.DISCORD_WEBHOOK_URL is None:
        logger.debug("DISCORD_WEBHOOK_URL not configured; skipping alert.")
        return

    webhook_url = settings.DISCORD_WEBHOOK_URL.get_secret_value()
    color = _SEVERITY_COLOR.get(incident_result.severity, 0x808080)

    fields: list[dict] = []
    if incident_result.deep_analysis is not None:
        fields.append(
            {
                "name": "Root Cause",
                "value": incident_result.deep_analysis.root_cause,
                "inline": False,
            }
        )
        actions_text = "\n".join(
            f"• {action}" for action in incident_result.deep_analysis.recommended_actions
        )
        fields.append(
            {
                "name": "Recommended Actions",
                "value": actions_text or "_No actions provided._",
                "inline": False,
            }
        )

    embed = {
        "title": f"[{incident_result.severity.name}] {incident_result.summary}",
        "description": incident_result.reasoning,
        "color": color,
        "fields": fields,
        "footer": {"text": "ChatOps Incident Agent"},
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json={"embeds": [embed]})
            response.raise_for_status()
        logger.info(
            "Discord alert sent: severity=%s summary=%r",
            incident_result.severity,
            incident_result.summary,
        )
    except Exception:
        logger.exception(
            "Failed to send Discord alert for severity=%s summary=%r",
            incident_result.severity,
            incident_result.summary,
        )
