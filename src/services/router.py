# src/services/router.py
import logging

from src.db.models import IncidentSeverity
from src.services.analysis_service import analyze_incident
from src.services.gemini_service import triage_incident
from src.services.schemas import IncidentAnalysisResult

logger = logging.getLogger(__name__)

_ESCALATE_SEVERITIES = {IncidentSeverity.P1_CRITICAL, IncidentSeverity.P2_HIGH}


async def route_incident(raw_payload: str) -> IncidentAnalysisResult:
    """Orchestrate the Gemini routing pipeline for an incoming incident payload.

    Always runs Tier-1 triage (gemini-2.0-flash). Escalates to Tier-2 deep
    analysis (gemini-1.5-pro) only when severity is P1_CRITICAL or P2_HIGH.
    """
    triage = await triage_incident(raw_payload)

    routed_to_claude = triage.severity in _ESCALATE_SEVERITIES
    logger.info(
        "Routing decision: severity=%s escalate=%s",
        triage.severity,
        routed_to_claude,
    )

    deep_analysis = None
    if routed_to_claude:
        deep_analysis = await analyze_incident(
            summary=triage.summary,
            raw_log=raw_payload,
            severity=triage.severity,
        )

    return IncidentAnalysisResult(
        summary=triage.summary,
        severity=triage.severity,
        reasoning=triage.reasoning,
        routed_to_claude=routed_to_claude,
        deep_analysis=deep_analysis,
    )
