from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from datetime import datetime

# Import models and schemas
from app.models import Query, QueryPriority, QueryStatus
from app.db.database import get_session
from app.utils.triage import calculate_priority, calculate_safety_score

# Import Pydantic models for request/response
from pydantic import BaseModel

# Define response models
class TriageResponse(BaseModel):
    query_id: int
    priority: str
    safety_score: float
    status: str

class TriageList(BaseModel):
    queries: List[TriageResponse]
    total: int

# Create router
router = APIRouter()

# Triage a specific query
@router.post("/{query_id}", response_model=TriageResponse)
async def triage_query(query_id: int, session: Session = Depends(get_session)):
    query = session.get(Query, query_id)
    if not query:
        raise HTTPException(status_code=404, detail="Query not found")
    
    # Calculate priority and safety score
    priority = calculate_priority(query.content)
    safety_score = calculate_safety_score(query.content)
    
    # Update query status to AWAITING_REVIEW after triage
    query.priority = priority
    query.safety_score = safety_score
    query.status = QueryStatus.AWAITING_REVIEW  # <-- This is critical
    query.updated_at = datetime.utcnow()
    
    session.add(query)
    session.commit()
    session.refresh(query)
    
    return TriageResponse(
        query_id=query.id,
        priority=query.priority.value,
        safety_score=query.safety_score,
        status=query.status.value
    )

# Get all triaged queries
@router.get("/", response_model=TriageList)
async def get_triaged_queries(
    priority: str = None,
    min_safety_score: float = None,
    max_safety_score: float = None,
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session)
):
    # Build query
    query = select(Query).where(Query.safety_score.is_not(None))
    
    # Apply filters if provided
    if priority:
        query = query.where(Query.priority == priority)
    if min_safety_score is not None:
        query = query.where(Query.safety_score >= min_safety_score)
    if max_safety_score is not None:
        query = query.where(Query.safety_score <= max_safety_score)
    
    # Get total count for pagination
    total = session.exec(query).all()
    total_count = len(total)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    results = session.exec(query).all()
    
    # Convert to response model
    triage_responses = [
        TriageResponse(
            query_id=q.id,
            priority=q.priority.value,
            safety_score=q.safety_score,
            status=q.status.value
        ) for q in results
    ]
    
    return TriageList(queries=triage_responses, total=total_count)

# Update priority for a query
@router.patch("/{query_id}/priority", response_model=TriageResponse)
async def update_query_priority(
    query_id: int,
    priority: QueryPriority,
    session: Session = Depends(get_session)
):
    # Get query from database
    query = session.get(Query, query_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found"
        )
    
    # Update priority
    query.priority = priority
    query.updated_at = datetime.utcnow()
    
    # Save changes
    session.add(query)
    session.commit()
    session.refresh(query)
    
    # Return updated triage info
    return TriageResponse(
        query_id=query.id,
        priority=query.priority.value,
        safety_score=query.safety_score or 0.0,
        status=query.status.value
    )
