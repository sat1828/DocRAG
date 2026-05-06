"""
Audit log model for tracking user actions and system events.
"""
from sqlalchemy import Column, String, DateTime, func, ForeignKey, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, Text
import json
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class AuditLog(Base):
    """Audit log for compliance and security tracking."""
    
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # upload, query, login, error, etc.
    details_json = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_logs_user_action", "user_id", "action"),
        Index("idx_audit_logs_timestamp", "timestamp"),
    )
    
    def __repr__(self):
        return f"<AuditLog(action='{self.action}', user_id={self.user_id})>"
