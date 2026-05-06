"""
Document upload and management router.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import uuid
import tempfile
from pathlib import Path
import aiofiles
import structlog

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.audit import AuditLog
from app.schemas.document import DocumentUploadResponse, DocumentResponse, DocumentListResponse
from app.services.ingestion import ingestion_service
from app.utils.validators import validate_pdf_file
from app.core.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = structlog.get_logger()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a PDF document for processing."""
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Save uploaded file temporarily
    temp_dir = Path(tempfile.gettempdir()) / "uploads"
    temp_dir.mkdir(exist_ok=True)
    
    temp_file = temp_dir / f"{uuid.uuid4()}_{file.filename}"
    
    try:
        async with aiofiles.open(temp_file, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Validate file
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > settings.MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit"
            )
        
        # Create document record
        doc_id = uuid.uuid4()
        new_doc = Document(
            id=doc_id,
            user_id=current_user.id,
            filename=file.filename,
            file_size=len(content),
            page_count=0,
            status="pending"
        )
        
        db.add(new_doc)
        await db.commit()
        
        # Create audit log
        audit_log = AuditLog(
            user_id=current_user.id,
            action="upload",
            details_json={"filename": file.filename, "doc_id": str(doc_id)}
        )
        db.add(audit_log)
        await db.commit()
        
        # Trigger async ingestion (pass file path, not session)
        import asyncio
        asyncio.create_task(
            process_document(temp_file, current_user.id, doc_id)
        )
        
        return DocumentUploadResponse(
            id=doc_id,
            filename=file.filename,
            status="processing",
            message="Document uploaded successfully. Processing in background."
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error("Upload failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload failed"
        )
    finally:
        # Clean up temp file AFTER background task starts
        # The background task will delete it after processing
        pass


async def process_document(file_path: Path, user_id: uuid.UUID, doc_id: uuid.UUID):
    """Background task to process document ingestion."""
    from app.core.database import async_session_factory
    
    try:
        # Create a new database session for background task
        async with async_session_factory() as db:
            # Update status to processing
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            
            if doc:
                doc.status = "processing"
                await db.commit()
                
                # Run ingestion
                ingest_result = await ingestion_service.ingest_pdf(
                    file_path=file_path,
                    user_id=str(user_id),
                    document_id=str(doc_id),
                    db_session=db
                )
                
                # Update document with results
                doc.status = "ready" if ingest_result["success"] else "error"
                doc.page_count = ingest_result.get("page_count", 0)
                doc.metadata_json = ingest_result.get("metadata", {})
                
                await db.commit()
                
                logger.info("Document processing completed", doc_id=str(doc_id))
            
    except Exception as e:
        logger.error("Document processing failed", error=str(e), doc_id=str(doc_id))
        
        # Update status to error
        async with async_session_factory() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc.status = "error"
                await db.commit()
    finally:
        # Clean up temp file after processing
        if file_path.exists():
            file_path.unlink()


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's documents with pagination."""
    # Get total count
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.user_id == current_user.id)
    )
    total = count_result.scalar()
    
    # Get documents
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    documents = result.scalars().all()
    
    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                file_size=doc.file_size,
                page_count=doc.page_count,
                status=doc.status,
                metadata_json=doc.metadata_json,
                created_at=doc.created_at
            )
            for doc in documents
        ],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific document details."""
    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.user_id == current_user.id
        )
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_size=doc.file_size,
        page_count=doc.page_count,
        status=doc.status,
        metadata_json=doc.metadata_json,
        created_at=doc.created_at
    )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    doc_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document and its embeddings."""
    result = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.user_id == current_user.id
        )
    )
    doc = result.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from ChromaDB
    from app.services.chroma_client import chroma_service
    chroma_service.delete_documents(
        collection_name=f"user_{current_user.id}",
        filter={"doc_id": str(doc_id)}
    )
    
    # Delete from database
    await db.delete(doc)
    await db.commit()
    
    return None
