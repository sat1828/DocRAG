"""
Document ingestion service using Docling for PDF parsing.
Handles text extraction, table detection, image processing, and chunking.
"""
from pathlib import Path
from typing import List, Dict, Any
import uuid
import structlog

# Lazy import for docling - only import when needed
try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    DocumentConverter = None
    InputFormat = None

from app.services.embeddings import embedding_service
from app.services.chroma_client import chroma_service
from app.services.gst_tools import gst_tools
from app.models.document import Document
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class DocumentIngestionService:
    """Service for ingesting and processing PDF documents."""
    
    def __init__(self):
        """Initialize Docling converter."""
        if DOCLING_AVAILABLE and DocumentConverter:
            self.converter = DocumentConverter(
                allowed_formats=[InputFormat.PDF]
            )
        else:
            self.converter = None
        self.chunk_size = 512
        self.chunk_overlap = 50
    
    async def ingest_pdf(
        self,
        file_path: Path,
        user_id: str,
        document_id: str,
        db_session: AsyncSession
    ) -> Dict[str, Any]:
        """
        Complete ingestion pipeline for a PDF document.
        
        Pipeline:
        1. Parse PDF with Docling
        2. Extract text, tables, images
        3. Chunk text (512 tokens, 50 overlap)
        4. Generate embeddings
        5. Store in ChromaDB
        6. Extract GST/legal metadata
        7. Update document record
        
        Args:
            file_path: Path to uploaded PDF
            user_id: User who uploaded
            document_id: Database document ID
            db_session: Database session
        
        Returns:
            Processing result metadata
        """
        logger.info("Starting PDF ingestion", file=str(file_path), user_id=user_id)
        
        try:
            # Step 1: Parse PDF with Docling
            logger.info("Parsing PDF with Docling")
            result = self.converter.convert(str(file_path))
            doc = result.document
            
            # Step 2: Extract structured content
            text_chunks = []
            metadatas = []
            chunk_ids = []
            
            page_count = len(doc.pages) if hasattr(doc, 'pages') else 0
            
            # Extract text from all pages
            full_text = doc.export_to_markdown() if hasattr(doc, 'export_to_markdown') else str(doc.texts)
            
            # Step 3: Chunk text
            chunks = self._chunk_text(full_text)
            
            for i, chunk in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                page_num = self._estimate_page_number(i, len(chunks), page_count)
                
                text_chunks.append(chunk)
                metadatas.append({
                    "user_id": str(user_id),
                    "doc_id": str(document_id),
                    "page_number": page_num,
                    "modality": "text",
                    "chunk_index": i,
                    "filename": file_path.name
                })
                chunk_ids.append(chunk_id)
            
            # Extract tables as HTML
            if hasattr(doc, 'tables') and doc.tables:
                for table_idx, table in enumerate(doc.tables):
                    table_html = str(table)  # Convert to HTML representation
                    chunk_id = f"{document_id}_table_{table_idx}"
                    
                    text_chunks.append(table_html)
                    metadatas.append({
                        "user_id": str(user_id),
                        "doc_id": str(document_id),
                        "page_number": table.page if hasattr(table, 'page') else 0,
                        "modality": "table",
                        "table_index": table_idx,
                        "filename": file_path.name
                    })
                    chunk_ids.append(chunk_id)
            
            # Step 4: Generate embeddings
            logger.info("Generating embeddings", chunk_count=len(text_chunks))
            embeddings = embedding_service.batch_embed(text_chunks, batch_size=32)
            
            # Step 5: Store in ChromaDB
            collection_name = f"user_{user_id}"
            chroma_service.add_documents(
                collection_name=collection_name,
                ids=chunk_ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=text_chunks
            )
            
            # Step 6: Extract GST and legal metadata
            logger.info("Extracting GST and legal metadata")
            gstins = gst_tools.extract_gstins(full_text)
            hsn_codes = gst_tools.extract_hsn_codes(full_text)
            legal_risks = gst_tools.flag_legal_risks(full_text)
            
            metadata_json = {
                "gstins": gstins,
                "hsn_codes": hsn_codes,
                "legal_risks": legal_risks,
                "page_count": page_count,
                "chunk_count": len(text_chunks),
                "has_tables": len(doc.tables) if hasattr(doc, 'tables') else 0
            }
            
            logger.info(
                "Ingestion completed",
                gstins=len(gstins),
                hsn_codes=len(hsn_codes),
                risks=len(legal_risks)
            )
            
            return {
                "success": True,
                "metadata": metadata_json,
                "chunk_count": len(text_chunks),
                "page_count": page_count
            }
            
        except Exception as e:
            logger.error("Ingestion failed", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Full document text
        
        Returns:
            List of text chunks
        """
        # Simple sentence-aware chunking
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk = " ".join(chunk_words)
            
            if len(chunk.strip()) > 50:  # Skip very small chunks
                chunks.append(chunk.strip())
        
        return chunks
    
    def _estimate_page_number(self, chunk_index: int, total_chunks: int, total_pages: int) -> int:
        """Estimate which page a chunk belongs to."""
        if total_pages == 0:
            return 0
        
        # Linear estimation
        page_num = int((chunk_index / max(total_chunks, 1)) * total_pages) + 1
        return min(page_num, total_pages)


# Singleton instance
ingestion_service = DocumentIngestionService()
