# Data model for telemetry storage

from pydantic import BaseModel, Field
from typing import Dict, Any

class TelemetryModel(BaseModel):
    drone_id: str
    position: Dict[str, float]
    battery: float
    status: str = Field(default="ok")
