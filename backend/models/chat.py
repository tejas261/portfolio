from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Session ID for conversation tracking")

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