# src/api/schemas.py

from typing import Any
from pydantic import BaseModel, Field


class IncomingWebhookPayload(BaseModel):
    source: str = Field(..., examples=["github", "pagerduty"])
    incident_id: str
    title: str
    description: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
