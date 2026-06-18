# src/services/analysis_service.py
import logging

from google import genai
from google.genai import types

from src.core.config import get_settings
from src.db.models import IncidentSeverity
from src.services.schemas import DeepAnalysisResult

logger = logging.getLogger(__name__)

_client: genai.Client | None = None

_ANALYSIS_SYSTEM_PROMPT = """You are a principal site reliability engineer performing deep-dive root cause analysis on a production incident.

Analyze the provided incident details and return a structured JSON response with exactly these fields:
- root_cause: A precise, technical explanation of the underlying cause of this incident.
- recommended_actions: A JSON array of 2-5 concrete, prioritised remediation steps (strings).
- confidence: Your confidence in this analysis — one of: "high", "medium", or "low".

Base your confidence on the completeness of the log data provided. Return ONLY the JSON object."""


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            api_key=get_settings().GEMINI_API_KEY.get_secret_value()
        )
    return _client


async def analyze_incident(
    summary: str,
    raw_log: str,
    severity: IncidentSeverity,
) -> DeepAnalysisResult:
    """Perform Tier-2 deep root cause analysis using Gemini Pro."""
    client = _get_client()
    contents = (
        f"Incident severity: {severity.value}\n"
        f"Triage summary: {summary}\n\n"
        f"Raw log / alert payload:\n{raw_log}"
    )
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_ANALYSIS_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=DeepAnalysisResult,
            ),
        )
        result = DeepAnalysisResult.model_validate_json(response.text)
        logger.info(
            "Gemini Pro analysis complete: confidence=%s actions=%d",
            result.confidence,
            len(result.recommended_actions),
        )
        return result
    except Exception as exc:
        logger.error("Gemini Pro deep analysis failed: %s", exc, exc_info=True)
        raise
