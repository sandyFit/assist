import os
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from sqlalchemy import select
from sqlmodel import Session
import httpx
from fastapi import HTTPException
from app.models import Query, AISuggestion, QueryStatus, File as FileModel
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv()

# Initialize DeepSeek client
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"

# General system prompt
GENERAL_SYSTEM_PROMPT = """
You are an AI medical assistant providing information to help doctors review patient queries.

Your role is to:
1. Provide factual, evidence-based information
2. Highlight areas of uncertainty
3. Suggest possible approaches or considerations
4. Flag any potential urgent concerns
5. NEVER provide definitive diagnoses or treatment recommendations

Your suggestions will be reviewed by a qualified medical professional before being shared with patients.

Format your response in a structured way with clear sections.
"""

# Diabetes-specific prompt
DIABETES_SYSTEM_PROMPT = """
You are an AI medical assistant specializing in diabetes care.

Your responsibilities:
1. Provide evidence-based information related to diabetes symptoms, management, and complications.
2. Highlight areas of uncertainty or where clinical follow-up is needed.
3. Suggest considerations for evaluating glycemic control, medication adherence, lifestyle, and complications.
4. Flag urgent concerns such as signs of ketoacidosis, hypoglycemia, or rapidly progressing neuropathy.
5. DO NOT provide definitive diagnoses or treatment plans.

All outputs will be reviewed by a qualified medical professional. 
Respond in a clear, structured format with headings like: Overview, Considerations, Urgent Concerns, Suggested Next Steps, and Notes.
"""

TYPE_1_PROMPT = """
You are an AI assistant focusing on Type 1 diabetes.

- Discuss insulin therapy, hypoglycemia risk, and glucose monitoring.
- Mention autoimmune causes if relevant.
- NEVER give treatment advice.
Respond with: Overview, Key Concerns, Possible Follow-ups, and Notes.
"""

TYPE_2_PROMPT = """
You are an AI assistant focusing on Type 2 diabetes.

- Discuss insulin resistance, lifestyle interventions, oral medications.
- Mention monitoring and complications such as neuropathy.
- NEVER give treatment advice.
Respond with: Overview, Key Concerns, Possible Follow-ups, and Notes.
"""


# Diabetes keyword list
DIABETES_KEYWORDS = [
    "sugar", "glucose", "thirsty", "blurred vision", "numb feet", "neuropathy",
    "insulin", "metformin", "blood sugar", "HbA1c", "ketoacidosis", "hypoglycemia"
]

TYPE_1_KEYWORDS = ["type 1", "insulin-dependent", "autoimmune", "juvenile"]
TYPE_2_KEYWORDS = ["type 2", "metformin", "lifestyle", "adult-onset", "insulin resistance"]

def get_diabetes_prompt(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in TYPE_1_KEYWORDS):
        return TYPE_1_PROMPT
    elif any(k in lowered for k in TYPE_2_KEYWORDS):
        return TYPE_2_PROMPT
    elif any(k in lowered for k in DIABETES_KEYWORDS):
        return DIABETES_SYSTEM_PROMPT
    else:
        return GENERAL_SYSTEM_PROMPT


def is_diabetes_related(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in DIABETES_KEYWORDS)

def extract_metrics_from_text(file_text: str) -> str:
    """
    Extract glucose-related metrics or flags from a given text.
    """
    lines = file_text.lower().splitlines()
    metrics = []

    for line in lines:
        if "glucose" in line or "mg/dl" in line or "mmol/l" in line:
            metrics.append(line.strip())
        elif "a1c" in line:
            metrics.append(line.strip())
        elif "insulin" in line and ("units" in line or "dose" in line):
            metrics.append(line.strip())

    return "\n".join(metrics) if metrics else "No key diabetes metrics detected."


def load_extracted_texts(query_id: int, session: Session) -> dict:
    """Load extracted text content from files associated with a query"""
    try:
        print(f"=== DEBUG: Loading extracted texts for query ID: {query_id} ===")
        
        # Validate input
        if not query_id or query_id <= 0:
            print(f"Invalid query_id: {query_id}")
            return {}
        
        if not session:
            print("Session is None")
            return {}
        
        # First, check if there are ANY files for this query
        all_files = session.exec(
            select(FileModel).where(FileModel.query_id == query_id)
        ).all()
        
        print(f"DEBUG: Found {len(all_files)} total files for query {query_id}")
        
        for file_obj in all_files:
            print(f"DEBUG: File - ID: {file_obj.id}, Name: {file_obj.filename}")
            print(f"DEBUG: Has text_content: {file_obj.text_content is not None}")
            if file_obj.text_content:
                print(f"DEBUG: Text content length: {len(file_obj.text_content)}")
                print(f"DEBUG: Text content preview: {file_obj.text_content[:200]}...")
            else:
                print(f"DEBUG: Text content is: {repr(file_obj.text_content)}")
        
        # Now filter for files with text content
        files_with_content = []
        for file_obj in all_files:
            if file_obj.text_content and file_obj.text_content.strip():
                files_with_content.append(file_obj)
                print(f"DEBUG: File {file_obj.filename} has valid content")
            else:
                print(f"DEBUG: File {file_obj.filename} has no valid content")
        
        print(f"DEBUG: Found {len(files_with_content)} files with valid text content")
        
        # Create the mapping from FileModel objects
        file_contents = {}
        for file_obj in files_with_content:
            if file_obj.filename:
                file_contents[file_obj.filename] = file_obj.text_content
                print(f"DEBUG: Added to results - {file_obj.filename}: {len(file_obj.text_content)} chars")
            else:
                print(f"DEBUG: Skipping file with no filename: ID {file_obj.id}")
        
        print(f"DEBUG: Final result contains {len(file_contents)} files")
        print(f"DEBUG: File names: {list(file_contents.keys())}")
        
        return file_contents
        
    except Exception as e:
        print(f"ERROR loading extracted texts for query {query_id}: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {}  # Return empty dict on any error
    

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_deepseek_api(messages: list, max_tokens: int = 1000) -> str:
    """Make HTTP request to DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tokens
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(DEEPSEEK_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
    except httpx.HTTPStatusError as e:
        error_msg = f"API Error {e.response.status_code}: {e.response.text}"
        raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

async def generate_suggestion(query, session: Session):
    """Generate an AI suggestion for a patient query"""
    try:
        print("=== ENTERING generate_suggestion ===")
        
        # Validate query parameter
        if query is None:
            raise ValueError("Query parameter is None")
            
        if not hasattr(query, 'id') or query.id is None:
            raise ValueError("Query object missing 'id' attribute or id is None")
            
        if not hasattr(query, 'content') or not query.content:
            raise ValueError("Query object missing 'content' attribute or content is empty")

        query_id = query.id
        query_content = query.content
        
        print(f"Processing query ID: {query_id}")
        
        # Check if suggestion already exists - use fresh query
        existing_suggestion = session.exec(
            select(AISuggestion).where(AISuggestion.query_id == query_id)
        ).first()
        
        if existing_suggestion:
            print(f"Suggestion already exists for query {query_id}")
            
            # Validate existing suggestion without trying to refresh
            if not existing_suggestion.id:
                print("WARNING: Existing suggestion has no ID, will create new one")
            elif not existing_suggestion.content:
                print("WARNING: Existing suggestion has no content, will create new one")
            else:
                print(f"Returning existing suggestion ID: {existing_suggestion.id}")
                return existing_suggestion

        # Generate new suggestion
        messages = [
            {"role": "system", "content": get_diabetes_prompt(query_content)},
            {"role": "user", "content": query_content}
        ]

        content = await call_deepseek_api(messages)
        
        suggestion = AISuggestion(
            query_id=query_id,
            content=content,
            model_used=DEFAULT_MODEL,
            confidence_score=0.8
        )

        # Update query status safely
        try:
            query.status = QueryStatus.AWAITING_REVIEW
            query.updated_at = datetime.utcnow()
            session.add(query)
        except Exception as update_error:
            print(f"Warning: Could not update query status: {str(update_error)}")

        session.add(suggestion)
        session.commit()
        session.refresh(suggestion)

        return suggestion
        
    except Exception as e:
        error_msg = f"Error generating suggestion: {str(e)}"
        print(f"FULL ERROR: {error_msg}")
        print(f"Exception type: {type(e).__name__}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        raise Exception(error_msg)

async def process_query_with_files(query: Query, file_contents: Dict[str, Any], session: Session) -> AISuggestion:
    """Generate an AI suggestion for a query with associated files"""
    try:
        # Validate query object
        if not query:
            raise ValueError("Query object is None")
        
        if not hasattr(query, 'id') or query.id is None:
            raise ValueError("Query object missing 'id' attribute or id is None")
            
        if not hasattr(query, 'content') or not query.content:
            raise ValueError("Query object missing 'content' attribute or content is empty")

        print(f"Processing query with files, ID: {query.id}")
        
        # Check if suggestion already exists - use fresh query
        existing_suggestion = session.exec(
            select(AISuggestion).where(AISuggestion.query_id == query.id)
        ).first()
        
        if existing_suggestion:
            print(f"Suggestion already exists for query {query.id}")
            
            # Validate existing suggestion without trying to refresh
            if not existing_suggestion.id:
                print("WARNING: Existing suggestion has no ID, will create new one")
            elif not existing_suggestion.content:
                print("WARNING: Existing suggestion has no content, will create new one")
            else:
                print(f"Returning existing suggestion ID: {existing_suggestion.id}")
                return existing_suggestion

        # Prepare file analysis (only if files exist)
        file_prompt = ""
        if file_contents:
            file_prompt = "\n\n📄 Attached Files Analysis:\n"
            for filename, content in file_contents.items():
                if content:  # Only process files with content
                    metrics = extract_metrics_from_text(content)
                    file_prompt += f"\n--- {filename} ---\n{metrics}\n"
        else:
            print("No file contents provided, generating suggestion based on query only")

        # Prepare messages for AI
        messages = [
            {"role": "system", "content": get_diabetes_prompt(query.content)},
            {"role": "user", "content": query.content + file_prompt}
        ]

        # Generate AI response
        ai_content = await call_deepseek_api(messages, max_tokens=1500)
        
        # Create new suggestion
        suggestion = AISuggestion(
            query_id=query.id,
            content=ai_content,
            model_used=DEFAULT_MODEL,
            confidence_score=0.75
        )

        # Update query status
        try:
            query.status = QueryStatus.AWAITING_REVIEW
            query.updated_at = datetime.utcnow()
            session.add(query)
        except Exception as query_update_error:
            print(f"Warning: Could not update query status: {str(query_update_error)}")
            # Don't fail the entire operation if query update fails

        # Save suggestion
        session.add(suggestion)
        
        try:
            session.commit()
            session.refresh(suggestion)
            
            # Verify the suggestion was properly saved
            if not suggestion.id:
                raise ValueError("Suggestion was not assigned an ID after commit")
                
        except Exception as commit_error:
            session.rollback()
            print(f"Database commit failed: {str(commit_error)}")
            raise ValueError(f"Failed to save suggestion to database: {str(commit_error)}")

        print(f"Successfully created new suggestion with ID: {suggestion.id}")
        return suggestion
        
    except Exception as e:
        print(f"Error processing query with files: {str(e)}")
        print(f"Query object type: {type(query)}")
        if query:
            print(f"Query ID: {getattr(query, 'id', 'NO_ID')}")
            print(f"Query content length: {len(getattr(query, 'content', ''))}")
        else:
            print("Query object is None")
        
        # Ensure we don't leave the session in a bad state
        try:
            session.rollback()
        except:
            pass
            
        raise
