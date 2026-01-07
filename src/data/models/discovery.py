from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class DiscoveryModel(BaseModel):
    client_id: str = Field(..., description="Unique identifier of the node (e.g., drone_01, gcs_01)")
    client_type: str = Field(..., description="Type of node: drone | ground | relay | sensor")
    software_version: str = Field(..., description="Software or firmware version running on the node")
    ip_address: Optional[str] = Field(None, description="IP address or reachable network address of the node")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities (e.g., ['video', 'telem', 'control'])")
    location: Optional[Dict[str, float]] = Field(
        default=None,
        description="Approximate location if available, e.g., {'lat': 28.67, 'lon': 77.21, 'alt': 50.0}"
    )
    uptime_seconds: Optional[int] = Field(None, description="Node uptime in seconds")
    status: str = Field(default="available", description="Current node status: available | busy | error | standby")
