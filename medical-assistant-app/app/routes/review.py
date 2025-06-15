from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

# Import models and schemas
from app.models import Review, Query, Doctor, QueryStatus, AISuggestion
from app.db.database import get_session

# Import Pydantic models for request/response
from pydantic import BaseModel

# Define request and response models
class ReviewCreate(BaseModel):
    doctor_id: int
    content: str
    approved: bool
    notes: Optional[str] = None

class ReviewResponse(BaseModel):
    id: int
    query_id: int
    doctor_id: int
    content: str
    approved: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class ReviewList(BaseModel):
    reviews: List[ReviewResponse]
    total: int

# Create router
router = APIRouter()

# Create a review for a query
@router.post("/{query_id}", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    query_id: int,
    review_data: ReviewCreate,
    session: Session = Depends(get_session)
):
    query = session.get(Query, query_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found"
        )
    
    if query.status != QueryStatus.AWAITING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Query with ID {query_id} is not awaiting review (current status: {query.status})"
        )
    
    doctor = session.get(Doctor, review_data.doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Doctor with ID {review_data.doctor_id} not found"
        )
    
    existing_review = session.exec(
        select(Review).where(Review.query_id == query_id)
    ).first()
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Review already exists for query with ID {query_id}"
        )
    
    review = Review(
        query_id=query_id,
        doctor_id=review_data.doctor_id,
        content=review_data.content,
        approved=review_data.approved,
        notes=review_data.notes
    )
    
    query.status = QueryStatus.REVIEWED
    query.updated_at = datetime.utcnow()
    
    session.add(review)
    session.add(query)
    session.commit()
    session.refresh(review)
    
    return ReviewResponse(
        id=review.id,
        query_id=review.query_id,
        doctor_id=review.doctor_id,
        content=review.content,
        approved=review.approved,
        notes=review.notes,
        created_at=review.created_at,
        updated_at=review.updated_at
    )

# Get all reviews with pagination
@router.get("/", response_model=ReviewList)
async def get_reviews(
    skip: int = 0,
    limit: int = 10,
    doctor_id: Optional[int] = None,
    approved: Optional[bool] = None,
    session: Session = Depends(get_session)
):
    query = select(Review)
    
    if doctor_id:
        query = query.where(Review.doctor_id == doctor_id)
    if approved is not None:
        query = query.where(Review.approved == approved)
    
    total = session.exec(query).all()
    total_count = len(total)
    
    query = query.offset(skip).limit(limit)
    results = session.exec(query).all()
    
    reviews = [
        ReviewResponse(
            id=r.id,
            query_id=r.query_id,
            doctor_id=r.doctor_id,
            content=r.content,
            approved=r.approved,
            notes=r.notes,
            created_at=r.created_at,
            updated_at=r.updated_at
        ) for r in results
    ]
    
    return ReviewList(reviews=reviews, total=total_count)

# Get a specific review by query ID
@router.get("/{query_id}", response_model=ReviewResponse)
async def get_review_by_query(
    query_id: int,
    session: Session = Depends(get_session)
):
    review = session.exec(
        select(Review).where(Review.query_id == query_id)
    ).first()
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No review found for query with ID {query_id}"
        )
    
    return ReviewResponse(
        id=review.id,
        query_id=review.query_id,
        doctor_id=review.doctor_id,
        content=review.content,
        approved=review.approved,
        notes=review.notes,
        created_at=review.created_at,
        updated_at=review.updated_at
    )

from app.llm.suggestion import process_query_with_files, load_extracted_texts

@router.post("/{query_id}/ai-suggestion", response_model=dict)
async def generate_ai_suggestion_with_files(
    query_id: int,
    session: Session = Depends(get_session)
):
    try:
        # Get the query
        query = session.get(Query, query_id)
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Query with ID {query_id} not found"
            )

        # Check if suggestion already exists - use fresh query to avoid session issues
        existing_suggestion = session.exec(
            select(AISuggestion).where(AISuggestion.query_id == query_id)
        ).first()
        
        if existing_suggestion:
            print(f"Suggestion already exists for query {query_id}, returning existing suggestion")
            
            # Instead of trying to refresh, validate the existing suggestion directly
            if not existing_suggestion.id:
                print("WARNING: Existing suggestion has no ID, will create new one")
            elif not existing_suggestion.content:
                print("WARNING: Existing suggestion has no content, will create new one")
            else:
                # Return the existing suggestion without attempting to refresh
                print(f"Successfully returning existing suggestion ID: {existing_suggestion.id}")
                return {
                    "suggestion_id": existing_suggestion.id,
                    "content": existing_suggestion.content,
                    "status": "success"
                }

        # If we reach here, we need to create a new suggestion
        # Load file contents
        file_contents = load_extracted_texts(query_id, session)

        # Generate suggestion - with or without files
        if file_contents:
            print(f"Processing query with {len(file_contents)} files")
            suggestion = await process_query_with_files(query, file_contents, session)
        else:
            print(f"No file contents found for query {query_id}")
            # Create a basic suggestion using the same logic but without files
            try:
                from app.llm.suggestion import generate_suggestion
                suggestion = await generate_suggestion(query, session)
            except ImportError:
                # If generate_suggestion is not available, use process_query_with_files with empty dict
                print("Falling back to process_query_with_files with empty file contents")
                suggestion = await process_query_with_files(query, {}, session)
        
        # Ensure we have a valid suggestion object
        if not suggestion:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate AI suggestion - suggestion is None"
            )
        
        # Validate suggestion attributes
        if not hasattr(suggestion, 'id') or suggestion.id is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generated suggestion has no valid ID"
            )
            
        if not hasattr(suggestion, 'content') or not suggestion.content:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generated suggestion has no content"
            )
        
        print(f"Successfully created new suggestion ID: {suggestion.id}")
        
        return {
            "suggestion_id": suggestion.id,
            "content": suggestion.content,
            "status": "success"
        }
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log the full error for debugging
        print(f"Unexpected error in generate_ai_suggestion_with_files: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
