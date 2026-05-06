"""
Chat schemas for query and history.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class QueryRequest(BaseModel):
    """Request schema for RAG query."""
    query: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[uuid.UUID] = None
    document_id: Optional[uuid.UUID] = None
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "query": "What is the total GST amount in this invoice?",
                "document_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }
    )


class SourceCitation(BaseModel):
    """Source citation for grounded answers."""
    page: int
    modality: str  # text, table, image
    snippet: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    document_id: Optional[uuid.UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class QueryResponse(BaseModel):
    """Response from RAG agent."""
    answer: str
    sources: List[SourceCitation]
    confidence: float = Field(..., ge=0.0, le=1.0)
    token_count: int
    hallucination_risk: str  # low, medium, high
    tool_calls: Optional[List[Dict[str, Any]]] = None
    response_time_ms: float
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "answer": "The total GST amount is ₹18,000 (9% CGST + 9% SGST on ₹1,00,000)",
                "sources": [{"page": 2, "modality": "table", "snippet": "GST: ₹18,000", "confidence": 0.95}],
                "confidence": 0.92,
                "token_count": 1247,
                "hallucination_risk": "low",
                "response_time_ms": 1850
            }
        }
    )


class ChatMessageResponse(BaseModel):
    """Chat message response."""
    id: uuid.UUID
    role: str
    content: str
    sources_json: Optional[List[SourceCitation]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ChatSessionResponse(BaseModel):
    """Chat session response."""
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    model_config = ConfigDict(from_attributes=True)
