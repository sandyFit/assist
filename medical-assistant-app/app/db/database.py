from sqlmodel import SQLModel, Session, create_engine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use default SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medical_assistant.db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    echo=False,  # Set to True to see SQL queries
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Function to create all tables in the database
def create_db_and_tables():
    """Create all tables defined in SQLModel models"""
    SQLModel.metadata.create_all(engine)

# Session dependency for FastAPI endpoints
def get_session():
    """Provide a database session for dependency injection in FastAPI routes"""
    with Session(engine) as session:
        yield session