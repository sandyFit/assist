from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from sqlmodel import Session, select  
from app.models import Patient, Doctor, Query, QueryStatus, QueryPriority
from app.db.database import create_db_and_tables, get_session, engine  

# Import routes
from app.routes import query, file, triage, review

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    create_db_and_tables()
    
    # Add test data - using regular synchronous session
    with Session(engine) as session:
        # Create test patient if none exists
        patient = session.exec(select(Patient).limit(1)).first()
        if not patient:
            patient = Patient(
                external_id="test123",
                name="Test Patient",
                email="test@example.com",
                age=30
            )
            session.add(patient)
            session.commit()
        
        # Create test doctor if none exists
        doctor = session.exec(select(Doctor).limit(1)).first()
        if not doctor:
            doctor = Doctor(
                external_id="doc123",
                name="Dr. Test",
                email="doctor@example.com",
                specialty="General"
            )
            session.add(doctor)
            session.commit()
        
        # Create test query if none exists
        query = session.exec(select(Query).limit(1)).first()
        if not query:
            query = Query(
                patient_id=patient.id,
                content="Test query about blood sugar",
                status=QueryStatus.AWAITING_REVIEW,
                priority=QueryPriority.MEDIUM
            )
            session.add(query)
            session.commit()
    
    yield

# Initialize FastAPI app
app = FastAPI(
    title="Medical AI Assistant API",
    description="API for a medical assistant demo with AI suggestions and doctor review",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For demo purposes; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router, prefix="/api/query", tags=["queries"])
app.include_router(file.router, prefix="/api/file", tags=["files"])
app.include_router(triage.router, prefix="/api/triage", tags=["triage"])
app.include_router(review.router, prefix="/api/review", tags=["review"])

# Root endpoint
@app.get("/", tags=["status"])
async def root():
    return {"status": "online", "message": "Medical AI Assistant API is running"}

# Health check endpoint
@app.get("/health", tags=["status"])
async def health_check():
    return {"status": "healthy"}

# Version endpoint
@app.get("/version", tags=["status"])
async def version():
    return {"version": app.version}

# Only run if not using reload
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "127.0.0.1")
    # Do NOT use reload=True here, use it via command line
    uvicorn.run("app.main:app", host=host, port=port)
