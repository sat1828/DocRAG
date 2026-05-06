"""
Document model for tracking uploaded PDFs and their metadata.
"""
from sqlalchemy import Column, String, Integer, Enum as SAEnum, DateTime, func, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Document(Base):
    """Document model for tracking PDF uploads and processing status."""
    
    __tablename__ = "documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    page_count = Column(Integer, nullable=False, default=0)
    status = Column(
        SAEnum("pending", "processing", "ready", "error", name="doc_status"),
        nullable=False,
        default="pending"
    )
    metadata_json = Column(JSON, nullable=True)  # GSTINs, HSNs, tax totals, risk flags
    chroma_collection_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chat_messages = relationship("ChatMessage", back_populates="document", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_documents_user_status", "user_id", "status"),
        Index("idx_documents_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<Document(filename='{self.filename}', status='{self.status}')>"
