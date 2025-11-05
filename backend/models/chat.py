from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ClientMeta(BaseModel):
    visitor_id: Optional[str] = Field(None, description="Anonymous visitor id")
    user_agent: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    referrer: Optional[str] = None
    page_url: Optional[str] = None
    dnt: Optional[bool] = Field(None, description="Do Not Track header")
    client_latency_ms: Optional[int] = None
    # Network and device hints from browser
    net_effective_type: Optional[str] = Field(None, description="navigator.connection.effectiveType")
    net_downlink: Optional[float] = Field(None, description="navigator.connection.downlink Mbps")
    net_rtt: Optional[int] = Field(None, description="navigator.connection.rtt ms")
    net_save_data: Optional[bool] = Field(None, description="navigator.connection.saveData")
    device_memory: Optional[float] = Field(None, description="navigator.deviceMemory GB")
    # Client-provided geolocation (if user granted permission)
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    geo_country: Optional[str] = None
    geo_region: Optional[str] = None
    geo_city: Optional[str] = None

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Session ID for conversation tracking")
    meta: Optional[ClientMeta] = Field(None, description="Optional client metadata for analytics")

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant response")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatMessage]