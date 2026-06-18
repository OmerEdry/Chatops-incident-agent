# src/services/schemas.py
from typing import Literal

from pydantic import BaseModel

from src.db.models import IncidentSeverity


class TriageResult(BaseModel):
    summary: str
    severity: IncidentSeverity
    reasoning: str


class DeepAnalysisResult(BaseModel):
    root_cause: str
    recommended_actions: list[str]
    confidence: Literal["high", "medium", "low"]


class IncidentAnalysisResult(BaseModel):
    summary: str
    severity: IncidentSeverity
    reasoning: str
    routed_to_claude: bool
    deep_analysis: DeepAnalysisResult | None = None
