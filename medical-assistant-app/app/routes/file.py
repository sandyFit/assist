from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from sqlmodel import Session, select
from typing import List, Optional
import os
import shutil
from datetime import datetime
import uuid
import PyPDF2
import io

# Import models and schemas
from app.models import File, Query
from app.db.database import get_session
from app.utils.file_validation import validate_file

# Import Pydantic models for request/response
from pydantic import BaseModel

# Define response models
class FileResponse(BaseModel):
    id: int
    query_id: int
    filename: str
    file_type: str
    file_size: int
    created_at: datetime
    text_content: Optional[str] = None  # Add this field

class FileList(BaseModel):
    files: List[FileResponse]
    total: int

# Create router
router = APIRouter()

# Upload directory
UPLOAD_DIR = os.path.join(os.getcwd(), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Utility functions for text extraction
def extract_text_from_pdf(content: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def extract_text_from_txt(content: bytes) -> str:
    """Extract text from TXT bytes"""
    try:
        return content.decode('utf-8')
    except Exception as e:
        print(f"Error extracting TXT text: {e}")
        return ""

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove any characters that aren't alphanumeric, dots, hyphens, or underscores
    sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
    return sanitized

# Upload a file for a specific query
@router.post("/{query_id}/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    query_id: int,
    file: UploadFile = FastAPIFile(...),
    session: Session = Depends(get_session)
):
    # 1. Validate file
    validation = validate_file(file)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["message"])
    
    # 2. Check query existence
    query = session.get(Query, query_id)
    if not query:
        raise HTTPException(status_code=404, detail=f"Query with ID {query_id} not found")
    
    # 3. Read contents and extract text
    contents = await file.read()
    ext = os.path.splitext(file.filename.lower())[1]
    
    extracted_text = ""
    if ext == ".pdf":
        extracted_text = extract_text_from_pdf(contents)
    elif ext == ".txt":
        extracted_text = extract_text_from_txt(contents)

    print("🧠 Extracted text from uploaded file:")
    print(extracted_text[:500])  # Show first 500 chars

    # 4. Save file to disk
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        buffer.write(contents)  # use the read content, not file.file

    file_size = os.path.getsize(file_path)

    # 5. Store file metadata in DB
    db_file = File(
        query_id=query_id,
        filename=sanitize_filename(file.filename),
        file_path=file_path,
        file_type=file.content_type,
        file_size=file_size,
        text_content=extracted_text  # 👈 Save the extracted text
    )

    session.add(db_file)
    session.commit()
    session.refresh(db_file)
    
    print("🧾 Extracted Text Content to be returned:")
    print(db_file.text_content[:500] if db_file.text_content else "No text content")

    return FileResponse(
        id=db_file.id,
        query_id=db_file.query_id,
        filename=db_file.filename,
        file_type=db_file.file_type,
        file_size=db_file.file_size,
        created_at=db_file.created_at,
        text_content=db_file.text_content  # Include text content in response
    )

# Get all files for a specific query
@router.get("/{query_id}", response_model=FileList)
async def get_files_for_query(
    query_id: int,
    session: Session = Depends(get_session)
):
    # Check if query exists
    query = session.get(Query, query_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found"
        )
    
    # Get files for query
    files_query = select(File).where(File.query_id == query_id)
    files = session.exec(files_query).all()
    
    # Convert to response model
    file_responses = [
        FileResponse(
            id=f.id,
            query_id=f.query_id,
            filename=f.filename,
            file_type=f.file_type,
            file_size=f.file_size,
            created_at=f.created_at,
            text_content=f.text_content
        ) for f in files
    ]
    
    return FileList(files=file_responses, total=len(file_responses))

# Delete a file
@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: int,
    session: Session = Depends(get_session)
):
    # Get file from database
    db_file = session.get(File, file_id)
    if not db_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {file_id} not found"
        )
    
    # Delete file from disk if it exists
    if os.path.exists(db_file.file_path):
        os.remove(db_file.file_path)
    
    # Delete from database
    session.delete(db_file)
    session.commit()
    
    return None
