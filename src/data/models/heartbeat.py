from pydantic import BaseModel, Field
from typing import Optional, Dict


class HeartbeatBlockModel(BaseModel):
    timestamp: float = Field(..., description="Unix timestamp when heartbeat was generated")
    
    cpu_usage: Optional[float] = Field(
        None, description="CPU usage percentage (0-100)"
    )
    
    ram_usage: Optional[float] = Field(
        None, description="RAM usage in MB or percentage depending on system"
    )
    
    temperature: Optional[float] = Field(
        None, description="Internal temperature in °C"
    )
    
    battery_level: Optional[float] = Field(
        None, description="Battery percentage (0-100) if available"
    )
    
    link_quality: Optional[str] = Field(
        None, description="Signal quality: good | fair | poor | lost"
    )
    
    mode: Optional[str] = Field(
        None, description="Operating mode (for UAV FC), e.g., GUIDED | AUTO | HOLD"
    )
    
    armed: Optional[bool] = Field(
        None, description="Arming state of flight controller"
    )
    
    extra: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional additional metrics (custom key-value pairs)"
    )


class HeartbeatModel(BaseModel):
    companion: HeartbeatBlockModel = Field(
        ..., description="Heartbeat block from companion computer/system"
    )

    uav: Optional[HeartbeatBlockModel] = Field(
        default=None,
        description="Heartbeat block from UAV flight controller, empty if unavailable"
    )

