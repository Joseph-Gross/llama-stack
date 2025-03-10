from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    property_type: Optional[str] = None
    location: Optional[str] = None
    price_range: Optional[str] = None
    additional_filters: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    property_suggestions: Optional[List[Dict[str, Any]]] = None
