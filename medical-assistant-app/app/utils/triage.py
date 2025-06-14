from app.models import QueryPriority
import re

# Keywords for priority levels
URGENT_KEYWORDS = [
    "emergency", "severe pain", "chest pain", "difficulty breathing", "unconscious",
    "seizure", "stroke", "heart attack", "bleeding heavily", "suicide", "overdose",
    "anaphylaxis", "allergic reaction", "can't breathe", "collapsed", "trauma",
    "accident", "head injury", "broken bone", "fracture", "poisoning"
]

HIGH_KEYWORDS = [
    "infection", "fever", "vomiting", "diarrhea", "dehydration", "pregnant",
    "pregnancy", "blood", "dizzy", "dizziness", "fainting", "chronic pain",
    "worsening", "deteriorating", "not improving", "getting worse", "medication",
    "side effect", "reaction", "rash", "swelling"
]

MEDIUM_KEYWORDS = [
    "persistent", "ongoing", "recurring", "chronic", "weeks", "days",
    "uncomfortable", "pain", "ache", "sore", "tired", "fatigue", "weakness",
    "concerned", "worried", "anxiety", "stress", "depression", "mental health"
]

# Safety concerns keywords
SAFETY_CONCERN_KEYWORDS = [
    "suicide", "self-harm", "hurt myself", "end my life", "kill myself",
    "overdose", "too many pills", "harm others", "hurt someone", "violent",
    "abuse", "domestic violence", "assault", "emergency", "urgent", "critical",
    "life-threatening", "dying", "death", "fatal", "severe", "extreme"
]

def calculate_priority(text: str) -> QueryPriority:
    """Calculate priority level based on text content"""
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Check for urgent keywords
    for keyword in URGENT_KEYWORDS:
        if keyword in text_lower:
            return QueryPriority.URGENT
    
    # Check for high priority keywords
    for keyword in HIGH_KEYWORDS:
        if keyword in text_lower:
            return QueryPriority.HIGH
    
    # Check for medium priority keywords
    for keyword in MEDIUM_KEYWORDS:
        if keyword in text_lower:
            return QueryPriority.MEDIUM
    
    # Default to low priority
    return QueryPriority.LOW

def calculate_safety_score(text: str) -> float:
    """Calculate safety score based on text content
    
    Returns a score between 0.0 and 1.0, where:
    - 0.0 means no safety concerns
    - 1.0 means highest level of safety concerns
    """
    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()
    
    # Initialize score
    score = 0.0
    
    # Check for safety concern keywords
    for keyword in SAFETY_CONCERN_KEYWORDS:
        if keyword in text_lower:
            # Increase score for each match
            score += 0.2
    
    # Cap score at 1.0
    return min(score, 1.0)

def should_escalate(text: str) -> bool:
    """Determine if a query should be escalated for immediate attention"""
    # Calculate safety score
    safety_score = calculate_safety_score(text)
    
    # Calculate priority
    priority = calculate_priority(text)
    
    # Escalate if safety score is high or priority is urgent
    return safety_score > 0.6 or priority == QueryPriority.URGENT
