from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

# Import models and schemas
from app.models import Query, QueryStatus, Patient, QueryPriority, AISuggestion
from app.db.database import get_session

# Import Pydantic models for request/response
from pydantic import BaseModel

# Define request and response models
class QueryCreate(BaseModel):
    patient_id: int
    content: str

class QueryResponse(BaseModel):
    id: int
    content: str
    status: str
    priority: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class QueryList(BaseModel):
    queries: List[QueryResponse]
    total: int

# Create router
router = APIRouter()

# Simple triage function (since we don't have the utils module)
def simple_triage(content: str) -> QueryPriority:
    """Simple triage based on keywords"""
    content_lower = content.lower()
    
    # Urgent keywords
    urgent_keywords = ['emergency', 'severe pain', 'chest pain', 'difficulty breathing', 'bleeding', 'unconscious']
    if any(keyword in content_lower for keyword in urgent_keywords):
        return QueryPriority.URGENT
    
    # High priority keywords
    high_keywords = ['pain', 'fever', 'infection', 'urgent', 'worried']
    if any(keyword in content_lower for keyword in high_keywords):
        return QueryPriority.HIGH
    
    # Medium priority keywords
    medium_keywords = ['symptoms', 'concern', 'question', 'advice']
    if any(keyword in content_lower for keyword in medium_keywords):
        return QueryPriority.MEDIUM
    
    return QueryPriority.LOW

# Simple AI suggestion generator
def generate_ai_suggestion(content: str) -> str:
    """Generate a simple AI suggestion for demo purposes"""
    content_lower = content.lower()
    
    if 'headache' in content_lower:
        return "For headaches, consider: 1) Rest in a quiet, dark room 2) Stay hydrated 3) Apply cold/warm compress 4) Over-the-counter pain relievers if appropriate. Seek immediate care if severe or accompanied by fever, stiff neck, or vision changes."
    
    elif 'fever' in content_lower:
        return "For fever management: 1) Stay hydrated 2) Rest 3) Monitor temperature regularly 4) Consider fever reducers if appropriate. Seek medical attention if fever is high (>101.3°F/38.5°C) or persists."
    
    elif 'cough' in content_lower:
        return "For cough symptoms: 1) Stay hydrated 2) Use honey or throat lozenges 3) Humidify air 4) Avoid irritants. Consult healthcare provider if cough persists >2 weeks, produces blood, or accompanied by fever/difficulty breathing."
    
    else:
        return "Based on your symptoms, I recommend monitoring your condition and consulting with a healthcare provider for proper evaluation and personalized medical advice. If symptoms worsen or you're concerned, seek medical attention promptly."

# Create a new query
@router.post("/", response_model=QueryResponse, status_code=status.HTTP_201_CREATED)
async def create_query(query_data: QueryCreate, session: Session = Depends(get_session)):
    # Check if patient exists
    patient = session.exec(select(Patient).where(Patient.id == query_data.patient_id)).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient with ID {query_data.patient_id} not found"
        )
    
    # Create new query with immediate triage
    priority = simple_triage(query_data.content)
    
    query = Query(
        patient_id=query_data.patient_id,
        content=query_data.content,
        status=QueryStatus.AWAITING_REVIEW,  # Skip PENDING, go straight to awaiting review
        priority=priority
    )
    
    session.add(query)
    session.commit()
    session.refresh(query)
    
    # Create AI suggestion
    ai_content = generate_ai_suggestion(query_data.content)
    ai_suggestion = AISuggestion(
        query_id=query.id,
        content=ai_content,
        model_used="demo_model",
        confidence_score=0.75
    )
    
    session.add(ai_suggestion)
    session.commit()
    
    # Return the created query
    return QueryResponse(
        id=query.id,
        content=query.content,
        status=query.status.value,
        priority=query.priority.value,
        created_at=query.created_at,
        updated_at=query.updated_at
    )

# Get all queries with pagination
@router.get("/", response_model=QueryList)
async def get_queries(
    skip: int = 0, 
    limit: int = 10, 
    status: Optional[str] = None,
    patient_id: Optional[int] = None,
    session: Session = Depends(get_session)
):
    # Build query
    query = select(Query)
    
    # Apply filters if provided
    if status:
        # Convert string status to enum for proper comparison
        try:
            status_enum = QueryStatus(status)
            query = query.where(Query.status == status_enum)
        except ValueError:
            # If invalid status provided, return empty result
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}. Valid statuses are: {[s.value for s in QueryStatus]}"
            )
    
    if patient_id:
        query = query.where(Query.patient_id == patient_id)
    
    # Get total count for pagination
    total = session.exec(query).all()
    total_count = len(total)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    results = session.exec(query).all()
    
    # Convert to response model
    queries = [
        QueryResponse(
            id=q.id,
            content=q.content,
            status=q.status.value,
            priority=q.priority.value,
            created_at=q.created_at,
            updated_at=q.updated_at
        ) for q in results
    ]
    
    return QueryList(queries=queries, total=total_count)

# Get a specific query by ID
@router.get("/{query_id}", response_model=QueryResponse)
async def get_query(query_id: int, session: Session = Depends(get_session)):
    query = session.get(Query, query_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found"
        )
    
    return QueryResponse(
        id=query.id,
        content=query.content,
        status=query.status.value,
        priority=query.priority.value,
        created_at=query.created_at,
        updated_at=query.updated_at
    )

# Update a query's status
@router.patch("/{query_id}/status", response_model=QueryResponse)
async def update_query_status(
    query_id: int, 
    new_status: QueryStatus,
    session: Session = Depends(get_session)
):
    query = session.get(Query, query_id)
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Query with ID {query_id} not found"
        )
    
    # Update status and timestamp
    query.status = new_status
    query.updated_at = datetime.utcnow()
    
    # Save changes
    session.add(query)
    session.commit()
    session.refresh(query)
    
    return QueryResponse(
        id=query.id,
        content=query.content,
        status=query.status.value,
        priority=query.priority.value,
        created_at=query.created_at,
        updated_at=query.updated_at
    )
