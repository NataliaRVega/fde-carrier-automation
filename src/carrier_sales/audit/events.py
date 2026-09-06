from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    event_type: str
    call_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    carrier_mc: str | None = None
    load_id: str | None = None
    agreed_rate: float | None = None
    outcome: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)