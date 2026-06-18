# src/services/gemini_service.py
import logging

from google import genai
from google.genai import types

from src.core.config import get_settings
from src.services.schemas import TriageResult

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

_TRIAGE_SYSTEM_PROMPT = """You are a senior site reliability engineer performing rapid incident triage.

Analyze the provided infrastructure log or alert and return a structured JSON response with exactly these fields:
- summary: A concise 1-2 sentence description of what happened and what is affected.
- severity: One of P1_CRITICAL, P2_HIGH, P3_WARNING, P4_INFO based on production impact.
- reasoning: A brief 1-2 sentence explanation of why you assigned this severity level.

Severity classification guide:
- P1_CRITICAL: Production system down, data loss risk, or widespread customer-facing outage.
- P2_HIGH: Major feature or service degraded, significant user impact, escalation required.
- P3_WARNING: Minor degradation or anomaly detected, no immediate user impact, warrants monitoring.
- P4_INFO: Informational event, scheduled activity, or noise — no action required."""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=get_settings().GEMINI_API_KEY.get_secret_value()
        )
    return _client


async def triage_incident(raw_log: str) -> TriageResult:
    """Classify an incident log using Gemini Flash for rapid Tier-1 triage."""
    client = _get_client()
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Analyze this incident log and return your triage assessment:\n\n{raw_log}",
            config=types.GenerateContentConfig(
                system_instruction=_TRIAGE_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=TriageResult,
            ),
        )
        result = TriageResult.model_validate_json(response.text)
        logger.info(
            "Gemini triage complete: severity=%s summary=%r",
            result.severity,
            result.summary[:80],
        )
        return result
    except Exception as exc:
        logger.error("Gemini triage failed: %s", exc, exc_info=True)
        raise
