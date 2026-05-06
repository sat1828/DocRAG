"""
Document schemas for upload and retrieval.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class DocumentUploadResponse(BaseModel):
    """Response after successful document upload."""
    id: uuid.UUID
    filename: str
    status: str
    message: str = "Document uploaded successfully. Processing in background."
    
    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    """Document information response."""
    id: uuid.UUID
    filename: str
    file_size: int
    page_count: int
    status: str
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """List of documents with pagination."""
    documents: List[DocumentResponse]
    total: int
    page: int
    per_page: int
