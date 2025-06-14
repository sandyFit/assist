from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile
from sqlmodel import Session, select
from typing import List
import os
import shutil
from datetime import datetime
import uuid

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

class FileList(BaseModel):
    files: List[FileResponse]
    total: int

# Create router
router = APIRouter()

# Upload directory
UPLOAD_DIR = os.path.join(os.getcwd(), "data", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Upload a file for a specific query
@router.post("/{query_id}/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    query_id: int,
    file: UploadFile = FastAPIFile(...),
    session: Session = Depends(get_session)
):
    # Check if query exists
    query = session.get(Query, query_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found"
        )
    
    # Validate file (type, size, etc.)
    validation_result = validate_file(file)
    if not validation_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result["message"]
        )
    
    # Generate unique filename to prevent collisions
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    # Create file record in database
    db_file = File(
        query_id=query_id,
        filename=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        file_size=file_size
    )
    
    # Add to database
    session.add(db_file)
    session.commit()
    session.refresh(db_file)
    
    # Return file info
    return FileResponse(
        id=db_file.id,
        query_id=db_file.query_id,
        filename=db_file.filename,
        file_type=db_file.file_type,
        file_size=db_file.file_size,
        created_at=db_file.created_at
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
            created_at=f.created_at
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
