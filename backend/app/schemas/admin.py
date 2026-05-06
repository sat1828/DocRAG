"""
Admin schemas for metrics and monitoring.
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class MetricsResponse(BaseModel):
    """System metrics for admin dashboard."""
    total_users: int
    total_documents: int
    total_queries: int
    avg_response_time_ms: float
    avg_confidence_score: float
    hallucination_rate: float  # Percentage
    retrieval_ndcg: float
    ragas_faithfulness: float
    ragas_answer_relevancy: float
    usage_last_7_days: List[Dict[str, Any]]


class UserStatsResponse(BaseModel):
    """User statistics."""
    id: str
    email: str
    role: str
    document_count: int
    query_count: int
    last_active: datetime
    created_at: datetime


class SystemHealthResponse(BaseModel):
    """System health check."""
    status: str  # healthy, degraded, unhealthy
    database: str
    chromadb: str
    ollama: str
    timestamp: datetime
