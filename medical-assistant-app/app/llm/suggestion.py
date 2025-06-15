import os
from datetime import datetime
from typing import Dict, Any, Optional
import openai
from dotenv import load_dotenv

# Import models
from app.models import Query, AISuggestion, QueryStatus
from sqlmodel import Session

# Load environment variables
load_dotenv()

# Configure OpenAI API
openai.api_key = os.getenv("OPENAI_API_KEY")

# Default model to use
DEFAULT_MODEL = "gpt-4"

# System prompt for medical assistant
SYSTEM_PROMPT = """
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

async def generate_suggestion(query: Query, session: Session) -> AISuggestion:
    """Generate an AI suggestion for a patient query"""
    try:
        # Extract query content
        query_content = query.content
        
        # Create messages for the API call
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query_content}
        ]
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=0.3,  # Lower temperature for more factual responses
            max_tokens=1000,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        # Extract suggestion content
        suggestion_content = response.choices[0].message.content
        
        # Calculate confidence score (simplified example)
        confidence_score = 0.7  # In a real system, this would be more sophisticated
        
        # Create AI suggestion record
        suggestion = AISuggestion(
            query_id=query.id,
            content=suggestion_content,
            model_used=DEFAULT_MODEL,
            confidence_score=confidence_score
        )
        
        # Update query status
        query.status = QueryStatus.AWAITING_REVIEW
        query.updated_at = datetime.utcnow()
        
        # Save to database
        session.add(suggestion)
        session.add(query)
        session.commit()
        session.refresh(suggestion)
        
        return suggestion
        
    except Exception as e:
        # Log the error
        print(f"Error generating suggestion: {str(e)}")
        raise

async def process_query_with_files(query: Query, file_contents: Dict[str, Any], session: Session) -> AISuggestion:
    """Generate an AI suggestion for a query with associated files"""
    try:
        # Extract query content
        query_content = query.content
        
        # Prepare file content for inclusion in the prompt
        file_prompt = "\n\nThe following files were uploaded with this query:\n\n"
        for filename, content in file_contents.items():
            file_prompt += f"--- {filename} ---\n{content}\n\n"
        
        # Create messages for the API call
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query_content + file_prompt}
        ]
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=DEFAULT_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=1500,  # Increased for file processing
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0
        )
        
        # Extract suggestion content
        suggestion_content = response.choices[0].message.content
        
        # Calculate confidence score (simplified example)
        confidence_score = 0.65  # Lower for file-based queries due to complexity
        
        # Create AI suggestion record
        suggestion = AISuggestion(
            query_id=query.id,
            content=suggestion_content,
            model_used=DEFAULT_MODEL,
            confidence_score=confidence_score
        )
        
        # Update query status
        query.status = QueryStatus.AWAITING_REVIEW
        query.updated_at = datetime.utcnow()
        
        # Save to database
        session.add(suggestion)
        session.add(query)
        session.commit()
        session.refresh(suggestion)
        
        return suggestion
        
    except Exception as e:
        # Log the error
        print(f"Error generating suggestion with files: {str(e)}")
        raise
