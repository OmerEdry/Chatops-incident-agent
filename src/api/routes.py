# src/api/routes.py
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from src.api.schemas import IncomingWebhookPayload
from src.services.discord import send_discord_alert
from src.services.router import route_incident
from src.services.schemas import IncidentAnalysisResult

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/api/v1/webhooks/incident",
    response_model=IncidentAnalysisResult,
    status_code=status.HTTP_200_OK,
)
async def handle_incident_webhook(
    payload: IncomingWebhookPayload,
    background_tasks: BackgroundTasks,
) -> IncidentAnalysisResult:
    context = (
        f"{payload.title}\n{payload.description}"
        if payload.description
        else payload.title
    )

    logger.info(
        "Received incident webhook: source=%s incident_id=%s",
        payload.source,
        payload.incident_id,
    )

    try:
        result = await route_incident(context)
    except Exception as exc:
        logger.exception(
            "AI pipeline failed for incident_id=%s",
            payload.incident_id,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Upstream AI service pipeline failed. Please retry.",
        ) from exc

    if result.routed_to_claude:
        background_tasks.add_task(send_discord_alert, result)

    return result
