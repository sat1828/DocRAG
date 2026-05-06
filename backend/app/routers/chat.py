"""
Chat router - handles RAG queries and conversation history.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.schemas.chat import (
    QueryRequest, QueryResponse, SourceCitation,
    ChatMessageResponse, ChatSessionResponse
)
from app.services.rag_agent import rag_agent

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = structlog.get_logger()


@router.post("/query", response_model=QueryResponse)
async def query_document(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Run RAG query on user's documents.
    Returns grounded answer with citations.
    """
    # If no session provided, create new one
    session_id = request.session_id
    
    if not session_id:
        # Create new session
        new_session = ChatSession(
            user_id=current_user.id,
            title=request.query[:100]  # Use first 100 chars as title
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        session_id = new_session.id
    
    # Verify session belongs to user
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Save user message
    user_message = ChatMessage(
        session_id=session_id,
        document_id=request.document_id,
        role="user",
        content=request.query
    )
    db.add(user_message)
    await db.commit()
    
    # Run RAG agent - handle errors gracefully
    try:
        response = await rag_agent.run(
            query=request.query,
            user_id=str(current_user.id),
            document_id=str(request.document_id) if request.document_id else None
        )
    except Exception as e:
        logger.error("RAG agent failed", error=str(e))
        response = {
            "answer": "I apologize, but I encountered an error processing your query. Please try again.",
            "sources": [],
            "confidence": 0.0,
            "token_count": 0,
            "hallucination_risk": "high",
            "tool_calls": [],
            "response_time_ms": 0
        }
    
    # Save assistant message
    assistant_message = ChatMessage(
        session_id=session_id,
        document_id=request.document_id,
        role="assistant",
        content=response["answer"],
        sources_json=response.get("sources", []),
        token_count=response.get("token_count", 0)
    )
    db.add(assistant_message)
    await db.commit()
    
    # Build response
    sources = [
        SourceCitation(**source)
        for source in response.get("sources", [])
    ]
    
    return QueryResponse(
        answer=response["answer"],
        sources=sources,
        confidence=response["confidence"],
        token_count=response.get("token_count", 0),
        hallucination_risk=response["hallucination_risk"],
        tool_calls=response.get("tool_calls"),
        response_time_ms=response["response_time_ms"]
    )


@router.get("/sessions", response_model=list[ChatSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's chat sessions."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    
    # Get message counts
    session_responses = []
    for session in sessions:
        count_result = await db.execute(
            select(func.count(ChatMessage.id)).where(ChatMessage.session_id == session.id)
        )
        message_count = count_result.scalar()
        
        session_responses.append(ChatSessionResponse(
            id=session.id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count
        ))
    
    return session_responses


@router.get("/history/{session_id}", response_model=list[ChatMessageResponse])
async def get_chat_history(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full conversation history for a session."""
    # Verify session ownership
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Get messages
    messages_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = messages_result.scalars().all()
    
    return [
        ChatMessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            sources_json=msg.sources_json,
            created_at=msg.created_at
        )
        for msg in messages
    ]


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    title: str = "New Chat",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session."""
    new_session = ChatSession(
        user_id=current_user.id,
        title=title[:500]
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return ChatSessionResponse(
        id=new_session.id,
        title=new_session.title,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
        message_count=0
    )
