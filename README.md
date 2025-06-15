
# 🩺 Assist AI - Medical Assistant Platform

A human-in-the-loop AI platform designed to bridge the communication gap between patients with chronic conditions and their doctors.

This project was developed for a hackathon to demonstrate how AI can empower healthcare professionals and reassure patients by acting as an intelligent, safe, and efficient intermediary. It provides a draft suggestion for patient queries which is always reviewed and approved by a doctor before being sent.

# 🖼️ Project Gallery

A brief look at the Patient and Doctor portals.

Patient Portal - Submit Query

Doctor Portal - Review Dashboard

(Insert screenshot of the patient query submission screen here)

(Insert screenshot of the doctor's dashboard with pending queries here)

# 🚀 The Problem

For millions living with chronic diseases like diabetes, timely access to their doctor for non-emergency questions is a constant challenge. A strange blood sugar reading or a question about a meal can cause significant anxiety. This "care gap" creates a communication bottleneck for doctors and leaves patients feeling uncertain. Assist AI was built to solve this problem.

# ✨ The Solution: How It Works

Assist AI provides a seamless and trustworthy workflow:

Patient Submits a Query: A patient logs into their portal and submits a health-related question, optionally attaching relevant documents like lab results.

AI Generates a Draft: The backend, powered by a LangGraph agent, receives the query. It fetches the patient's specific medical history and uses an LLM (DeepSeek) to generate a safe, empathetic, and informative draft response.

Doctor Reviews & Approves: This AI-generated draft is never sent directly to the patient. Instead, it appears on the doctor's secure dashboard for review. The doctor has full control to approve, edit, or completely rewrite the response.

Patient Receives Verified Advice: Only after the doctor approves the final message is it sent to the patient and logged in their history, ensuring all advice is medically sound and verified.

核心功能 (Core Features)
Dual-Role Interface: Separate, secure portals for Patients and Doctors.

Intelligent Query Processing: An AI agent that considers patient history to provide context-aware suggestions.

Doctor-in-the-Loop: Ensures 100% human verification of all medical advice.

Query Management: A dashboard for doctors to review pending queries and approve responses.

Patient History: A view for patients to see their past submissions and the doctor's final responses.

## 🛠️ Tech Stack
Backend:

Framework: FastAPI

AI Orchestration: LangGraph

LLM: DeepSeek (via an OpenAI-compatible API)

Data Validation: Pydantic

## Frontend:

Framework: Streamlit

Core Language: Python

📂 Project Structure
The project is organized into two main components for a clean separation of concerns:

hackathon-demo-assist/
├── backend_service/        # FastAPI backend, LangGraph agent, and all core logic
│   ├── main.py             # API endpoints
│   ├── graph.py            # LangGraph workflow definition
│   ├── pending_queries.py  # Logic for saving/loading queries
│   ├── patient_db.py       # Mock patient database
│   └── ...
└── assistMVP/
    └── streamlit_app/      # All frontend Streamlit files
        ├── main.py         # Main UI layout and role selection
        ├── patient.py      # Patient portal UI
        └── doctor.py       # Doctor dashboard UI

## 🏃 Getting Started
To run the application locally, you'll need to set up the environment and run both the backend and frontend services concurrently.

#### Prerequisites
Python 3.9+

An LLM API Key (e.g., from DeepSeek)

#### Installation & Setup
Clone the repository:

git clone [https://github.com/your-username/hackathon-demo-assist.git](https://github.com/your-username/hackathon-demo-assist.git)
cd hackathon-demo-assist

Set up the Backend:

Install backend dependencies:

pip install -r backend_service/requirements.txt

Create an environment file by copying the example:

cp backend_service/.env.example backend_service/.env

Edit backend_service/.env and add your DeepSeek API key and base URL.

Set up the Frontend:

Install frontend dependencies:

pip install -r assistMVP/streamlit_app/requirements.txt

Running the Application
You need to open two separate terminals.

Terminal 1: Start the Backend Server

Navigate to the project root (hackathon-demo-assist) and run:

python -m uvicorn backend_service.main:app --reload --port 8000

The backend will be running on http://localhost:8000.

Terminal 2: Start the Frontend Application

Navigate to the same project root (hackathon-demo-assist) and run:

streamlit run assistMVP/streamlit_app/main.py --server.port 8502

The frontend will be accessible at http://localhost:8502.

## 🌐 API Endpoints
The backend provides the following key API endpoints:

Method

Endpoint

Description

POST

/process_query/

Submits a new patient query for AI processing.

GET

/pending_queries/

Fetches all queries awaiting a doctor's review.

POST

/update_query/{query_id}

Updates a query's status (e.g., to "approved").

GET

/queries/by_patient/{patient_id}

Fetches the complete history for a specific patient.

## 🔮 Future Work
Persistent Database: Replace the in-memory/JSON storage with a robust database like PostgreSQL or MongoDB.

Real-time Notifications: Implement WebSockets to notify doctors instantly when a new query arrives.

Authentication & Security: Add a proper user authentication system (e.g., JWT or OAuth).

File Uploads: Fully implement the handling of uploaded medical documents.

Expanded Disease Models: Scale the platform to support additional chronic conditions beyond diabetes.

Analytics Dashboard: Provide insights for doctors on query volumes and response times.

## 👥 The Team
Patrick Musyoka - Team Leader / Backend Developer

Min Thiha Tun - Backend Developer

Patricia Ramos - Graphic Designer / Frontend Developer

Eman Rashid - Presentation and  Documentation

# Medical AI Assistant Demo App

A hackathon project demonstrating a medical AI assistant with FastAPI backend and Streamlit frontend. This application supports structured patient queries, file uploads, AI-assisted suggestions, and doctor-reviewed responses.

## Key Features

- **Patient Query Interface**: Submit structured medical questions
- **File Upload**: Share medical documents for AI analysis
- **Triage System**: Automatic prioritization of queries
- **Doctor Review**: Human oversight of all AI-generated responses
- **Role-Based UI**: Different interfaces for patients and medical professionals

## Design Philosophy

This application prioritizes safety and oversight over autonomy. While it leverages AI to generate suggestions, all outputs are reviewed by human doctors before being sent to patients. The system is designed to:

1. **Augment, not replace**: AI assists medical professionals rather than making autonomous decisions
2. **Ensure oversight**: All AI suggestions require human review
3. **Maintain transparency**: Clear indication of which content is AI-generated vs. human-verified
4. **Prioritize safety**: Triage system flags urgent or sensitive queries for immediate attention

## Setup Instructions

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

1. Clone the repository
2. Create and activate a virtual environment (optional but recommended)
   ```
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Unix/MacOS
   ```
3. Install dependencies
   ```
   pip install -r requirements.txt
   ```
4. Copy the environment template and configure your settings
   ```
   copy .env.example .env  # Windows
   cp .env.example .env    # Unix/MacOS
   ```
5. Edit the `.env` file with your API keys and configuration

### Running the Application

1. Seed the database with demo data
   ```
   python seed_db.py
   ```

2. Start the FastAPI backend
   ```
   uvicorn app.main:app --reload
   ```

3. In a separate terminal, start the Streamlit frontend
   ```
   streamlit run ui/frontend.py
   ```

4. Access the application:
   - API documentation: http://localhost:8000/docs
   - Streamlit UI: http://localhost:8501

## Project Structure

```
/medical-assistant-app/
├── app/
│   ├── main.py                # FastAPI entrypoint
│   ├── routes/                # API endpoints (query, file, triage, review)
│   ├── models/                # SQLModel or SQLAlchemy schemas
│   ├── db/                    # Database connection and seeding logic
│   ├── llm/                   # LLM integration functions
│   ├── utils/                 # Helpers like triage scoring or file validation
├── ui/
│   ├── frontend.py           # Role-based UI using Streamlit
│   ├── components/            # Reusable UI elements
├── tests/
│   ├── test_api.py           # Tests for backend routes
│   ├── test_safety.py        # Tests for AI safety scoring logic
├── data/                      # Sample input files for demo (PDFs, CSVs)
├── docs/                      # Uploaded prompts, compliance notes, and strategy
├── mcp-flow.yaml              # Optional — describes tool orchestration if used
├── seed_db.py                 # Script to populate mock demo data
├── README.md                  # Setup and usage instructions
├── requirements.txt           # Python dependencies
├── .env.example               # Sample config for API keys and settings
```

## MCP Integration

This project is compatible with MCP integration in the Trae IDE, but deliberately avoids using agents for medical decisions. The system architecture ensures that all AI-generated content is reviewed by qualified medical professionals before being presented to patients.

## License

This project is intended for demonstration purposes only and should not be used for actual medical advice.

