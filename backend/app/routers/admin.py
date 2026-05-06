"""
Admin router - metrics, monitoring, and user management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import structlog

from app.core.database import get_db
from app.core.security import require_admin
from app.models.user import User
from app.models.document import Document
from app.models.chat import ChatMessage
from app.models.audit import AuditLog
from app.schemas.admin import MetricsResponse, UserStatsResponse, SystemHealthResponse

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = structlog.get_logger()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get system-wide metrics for admin dashboard."""
    # Total users
    users_count = await db.execute(select(func.count(User.id)))
    total_users = users_count.scalar()
    
    # Total documents
    docs_count = await db.execute(select(func.count(Document.id)))
    total_documents = docs_count.scalar()
    
    # Total queries (assistant messages)
    queries_count = await db.execute(
        select(func.count(ChatMessage.id)).where(ChatMessage.role == "assistant")
    )
    total_queries = queries_count.scalar()
    
    # Usage last 7 days
    seven_days_ago = datetime.now(datetime.UTC) - timedelta(days=7)
    usage_result = await db.execute(
        select(func.date(AuditLog.timestamp), func.count(AuditLog.id))
        .where(AuditLog.timestamp >= seven_days_ago)
        .group_by(func.date(AuditLog.timestamp))
    )
    usage_data = [
        {"date": str(row[0]), "count": row[1]}
        for row in usage_result.all()
    ]
    
    # Placeholder metrics (would come from RAGAS eval in production)
    return MetricsResponse(
        total_users=total_users,
        total_documents=total_documents,
        total_queries=total_queries,
        avg_response_time_ms=1850.0,
        avg_confidence_score=0.87,
        hallucination_rate=2.5,
        retrieval_ndcg=0.87,
        ragas_faithfulness=0.92,
        ragas_answer_relevancy=0.89,
        usage_last_7_days=usage_data
    )


@router.get("/users", response_model=list[UserStatsResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users with activity stats."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    
    user_stats = []
    for user in users:
        # Document count
        doc_count = await db.execute(
            select(func.count(Document.id)).where(Document.user_id == user.id)
        )
        
        # Query count
        query_count = await db.execute(
            select(func.count(ChatMessage.id))
            .join(ChatMessage.session)
            .where(ChatMessage.session.has(user_id=user.id))
        )
        
        # Last active
        last_activity = await db.execute(
            select(func.max(AuditLog.timestamp))
            .where(AuditLog.user_id == user.id)
        )
        
        user_stats.append(UserStatsResponse(
            id=str(user.id),
            email=user.email,
            role=user.role,
            document_count=doc_count.scalar(),
            query_count=query_count.scalar(),
            last_active=last_activity.scalar() or user.created_at,
            created_at=user.created_at
        ))
    
    return user_stats


@router.get("/health", response_model=SystemHealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """System health check."""
    # Check database
    try:
        await db.execute(select(1))
        db_status = "healthy"
    except Exception as e:
        db_status = "unhealthy"
        logger.error("Database health check failed", error=str(e))
    
    # Check ChromaDB
    try:
        from app.services.chroma_client import chroma_service
        chroma_service.client.heartbeat()
        chroma_status = "healthy"
    except Exception as e:
        chroma_status = "unhealthy"
        logger.error("ChromaDB health check failed", error=str(e))
    
    # Check Ollama
    try:
        import httpx
        from app.core.config import settings
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5.0)
            ollama_status = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception as e:
        ollama_status = "unhealthy"
        logger.error("Ollama health check failed", error=str(e))
    
    # Overall status
    all_healthy = db_status == "healthy" and chroma_status == "healthy" and ollama_status == "healthy"
    overall_status = "healthy" if all_healthy else "degraded"
    
    return SystemHealthResponse(
        status=overall_status,
        database=db_status,
        chromadb=chroma_status,
        ollama=ollama_status,
        timestamp=datetime.now(datetime.UTC)
    )
