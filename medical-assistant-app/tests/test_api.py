import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.db.database import get_session
from app.models import Patient, Doctor, Query, QueryStatus, QueryPriority

# Create in-memory SQLite database for testing
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

# Create test client with dependency override
@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# Create test data
@pytest.fixture(name="test_data")
def test_data_fixture(session: Session):
    # Create test patient
    patient = Patient(external_id="test123", name="Test Patient", email="test@example.com", age=30)
    session.add(patient)
    
    # Create test doctor
    doctor = Doctor(external_id="doc123", name="Test Doctor", email="doctor@example.com", specialty="General Practice")
    session.add(doctor)
    
    # Create test queries
    queries = [
        Query(
            patient_id=1,
            content="I have a headache that won't go away after 3 days",
            status=QueryStatus.PENDING,
            priority=QueryPriority.MEDIUM
        ),
        Query(
            patient_id=1,
            content="My ankle is swollen after I twisted it yesterday",
            status=QueryStatus.PROCESSING,
            priority=QueryPriority.LOW
        )
    ]
    for query in queries:
        session.add(query)
    
    session.commit()
    
    return {"patient": patient, "doctor": doctor, "queries": queries}

# Test root endpoint
def test_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

# Test health check endpoint
def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

# Test creating a query
def test_create_query(client: TestClient, test_data):
    response = client.post(
        "/api/query/",
        json={
            "patient_id": test_data["patient"].id,
            "content": "I'm experiencing shortness of breath"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "I'm experiencing shortness of breath"
    assert data["status"] == "pending"

# Test getting all queries
def test_get_queries(client: TestClient, test_data):
    response = client.get("/api/query/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["queries"]) == 2

# Test getting a specific query
def test_get_query(client: TestClient, test_data):
    query_id = test_data["queries"][0].id
    response = client.get(f"/api/query/{query_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == query_id
    assert data["content"] == "I have a headache that won't go away after 3 days"

# Test updating a query's status
def test_update_query_status(client: TestClient, test_data):
    query_id = test_data["queries"][0].id
    response = client.patch(
        f"/api/query/{query_id}/status",
        json={"new_status": "processing"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"

# Test triaging a query
def test_triage_query(client: TestClient, test_data):
    query_id = test_data["queries"][0].id
    response = client.post(f"/api/triage/{query_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["query_id"] == query_id
    assert "safety_score" in data
    assert data["status"] == "processing"

# Test creating a review
def test_create_review(client: TestClient, test_data, session: Session):
    # First, update query status to awaiting_review
    query = test_data["queries"][0]
    query.status = QueryStatus.AWAITING_REVIEW
    session.add(query)
    session.commit()
    
    # Create a review
    response = client.post(
        f"/api/review/{query.id}",
        json={
            "doctor_id": test_data["doctor"].id,
            "content": "This appears to be a tension headache. I recommend rest and over-the-counter pain medication.",
            "approved": True,
            "notes": "Patient history shows previous similar episodes."
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["query_id"] == query.id
    assert data["approved"] == True
    
    # Check that query status was updated
    query_response = client.get(f"/api/query/{query.id}")
    assert query_response.json()["status"] == "reviewed"