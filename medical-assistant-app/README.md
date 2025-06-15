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