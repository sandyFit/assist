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
