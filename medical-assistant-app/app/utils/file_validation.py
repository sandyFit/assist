from fastapi import UploadFile
import os
from typing import Dict, Any
import fitz  # PyMuPDF

# Maximum file size (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file types
ALLOWED_EXTENSIONS = {
    # Documents
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    
    # Images
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    
    # Data
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".xls": "application/vnd.ms-excel",
}

def validate_file(file: UploadFile) -> Dict[str, Any]:
    """Validate uploaded file for type and size
    
    Returns a dictionary with:
    - valid: Boolean indicating if file is valid
    - message: Error message if invalid, success message if valid
    """
    # Check if file is empty
    if not file.filename:
        return {
            "valid": False,
            "message": "No file provided"
        }
    
    # Check file extension
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in ALLOWED_EXTENSIONS:
        return {
            "valid": False,
            "message": f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        }
    
    # Check content type
    expected_content_type = ALLOWED_EXTENSIONS.get(file_ext)
    if file.content_type != expected_content_type and not (
        # Special case for some content types that might vary
        file_ext == ".txt" and file.content_type.startswith("text/")
    ):
        return {
            "valid": False,
            "message": f"Invalid content type. Expected {expected_content_type}, got {file.content_type}"
        }
    
    # Check file size
    # Note: This requires reading the file into memory, which could be problematic for large files
    # In a production system, you might want to use a streaming approach
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)  # Reset file pointer
    
    if file_size > MAX_FILE_SIZE:
        return {
            "valid": False,
            "message": f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024} MB"
        }
    
    # All checks passed
    return {
        "valid": True,
        "message": "File is valid"
    }
    
def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n".join([page.get_text() for page in doc])

def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")

def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and other security issues"""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace potentially dangerous characters
    filename = filename.replace("/", "_").replace("\\", "_")
    
    return filename
