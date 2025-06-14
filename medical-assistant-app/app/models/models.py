from sqlmodel import SQLModel, Field, Relationship 
from typing import Optional, List
from datetime import datetime
import enum

SQLModel.metadata.clear()  
# Enum for query status
class QueryStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_REVIEW = "awaiting_review"
    REVIEWED = "reviewed"
    COMPLETED = "completed"

# Enum for query priority
class QueryPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Base model for common fields
class TimestampModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)

# Patient model
class Patient(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, unique=True)
    name: str
    email: str = Field(index=True)
    age: Optional[int] = None
    
    # Relationships
    queries: List["Query"] = Relationship(back_populates="patient")

# Doctor model
class Doctor(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, unique=True)
    name: str
    email: str = Field(index=True)
    specialty: Optional[str] = None
    
    # Relationships
    reviews: List["Review"] = Relationship(back_populates="doctor")

# Query model for patient questions
class Query(TimestampModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int = Field(foreign_key="patient.id")
    content: str
    status: QueryStatus = Field(default=QueryStatus.PENDING)
    priority: QueryPriority = Field(default=QueryPriority.MEDIUM)
    safety_score: Optional[float] = Field(default=None)
    
    # Relationships
    patient: Patient = Relationship(back_populates="queries")
    files: List["File"] = Relationship(back_populates="query")
    ai_suggestion: Optional["AISuggestion"] = Relationship(back_populates="query")
    review: Optional["Review"] = Relationship(back_populates="query")

# File model for uploaded documents
class File(TimestampModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="query.id")
    filename: str
    file_path: str
    file_type: str
    file_size: int
    text_content: Optional[str] = None
    
    # Relationships
    query: Query = Relationship(back_populates="files")

# AI Suggestion model
class AISuggestion(TimestampModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="query.id", unique=True)
    content: str
    model_used: str
    confidence_score: Optional[float] = None
    
    # Relationships
    query: Query = Relationship(back_populates="ai_suggestion")

# Review model for doctor reviews
class Review(TimestampModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="query.id", unique=True)
    doctor_id: int = Field(foreign_key="doctor.id")
    content: str
    approved: bool = Field(default=False)
    notes: Optional[str] = None
    
    # Relationships
    query: Query = Relationship(back_populates="review")
    doctor: Doctor = Relationship(back_populates="reviews")
