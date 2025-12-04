from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class ConversationSummary(BaseModel):
    """Summary view for admin - basic info and optional summary"""
    sessionId: str
    timestamp: str
    userId: str
    question: str
    response: str  # Full response text (always included)
    summary: Optional[Dict[str, Any]] = None  # Optional: category, topics, response_type, key_points (if Step 2.2 implemented)
    messageType: str

class ConversationResponse(BaseModel):
    """Full conversation details"""
    sessionId: str
    timestamp: str
    userId: str
    question: str
    response: str
    summary: Optional[Dict[str, Any]] = None  # Optional: only if Step 2.2 implemented
    messageType: str
    metadata: Optional[Dict] = None

class ConversationStats(BaseModel):
    """Conversation statistics"""
    total_conversations: int
    conversations_by_category: Dict[str, int]  # Empty if Step 2.2 not implemented
    conversations_by_date: Dict[str, int]  # Always available
    top_topics: List[Dict[str, int]]  # Empty if Step 2.2 not implemented

