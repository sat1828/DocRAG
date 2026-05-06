"""
Chat models for tracking conversation sessions and messages.
"""
from sqlalchemy import Column, String, Text, Integer, DateTime, func, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class ChatSession(Base):
    """Chat session model for grouping related messages."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(500), nullable=True, default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan",
                          order_by="ChatMessage.created_at")
    
    __table_args__ = (
        Index("idx_chat_sessions_user", "user_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<ChatSession(title='{self.title}')>"


class ChatMessage(Base):
    """Individual chat message with sources and metadata."""
    
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    sources_json = Column(JSON, nullable=True)  # Page numbers, snippets, confidence scores
    token_count = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    document = relationship("Document", back_populates="chat_messages")
    
    __table_args__ = (
        Index("idx_chat_messages_session", "session_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<ChatMessage(role='{self.role}', tokens={self.token_count})>"
