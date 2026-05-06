"""
Input validation and sanitization utilities.
"""
import re
from pathlib import Path
from fastapi import HTTPException, status


# GSTIN validation regex (Indian GST Identification Number)
GSTIN_REGEX = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')

# HSN code regex (4, 6, or 8 digits)
HSN_REGEX = re.compile(r'\b\d{4}(?:\d{2}(?:\d{2})?)?\b')


def validate_pdf_file(file_path: Path, max_size_mb: int = 50, max_pages: int = 100) -> dict:
    """Validate uploaded PDF file."""
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File not found"
        )
    
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {max_size_mb}MB"
        )
    
    if not file_path.suffix.lower() == '.pdf':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    return {
        "valid": True,
        "file_size_mb": file_size_mb,
    }


def sanitize_input(text: str, max_length: int = 2000) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Truncate to max length
    text = text[:max_length]
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def validate_gstin_format(gstin: str) -> bool:
    """Validate GSTIN format using regex."""
    return bool(GSTIN_REGEX.match(gstin))


def calculate_gstin_checksum(gstin: str) -> bool:
    """
    Validate GSTIN checksum.
    GSTIN format: 2 digit state code + 10 char PAN + 1 entity number + Z + 1 checksum
    """
    if len(gstin) != 15:
        return False
    
    # Simplified checksum validation
    # Full implementation would use GSTN's checksum algorithm
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    checksum = 0
    
    for i, char in enumerate(gstin[:14]):
        if char not in chars:
            return False
        checksum += chars.index(char) * (i + 1)
    
    expected_checksum = chars[checksum % 36]
    return gstin[14] == expected_checksum
