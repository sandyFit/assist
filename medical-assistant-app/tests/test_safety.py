import pytest
from app.utils.triage import calculate_priority, calculate_safety_score, should_escalate
from app.models import QueryPriority

# Test priority calculation
def test_calculate_priority_urgent():
    # Test urgent priority detection
    urgent_queries = [
        "I'm having severe chest pain and difficulty breathing",
        "My child is having a seizure",
        "I think I'm having a heart attack",
        "I'm bleeding heavily after surgery",
        "I'm having an allergic reaction and my throat is closing up"
    ]
    
    for query in urgent_queries:
        assert calculate_priority(query) == QueryPriority.URGENT

def test_calculate_priority_high():
    # Test high priority detection
    high_queries = [
        "I have a high fever that's not going down with medication",
        "I've been vomiting for two days and can't keep anything down",
        "I'm pregnant and experiencing unusual pain",
        "My medication is causing a rash all over my body",
        "I'm dizzy and feel like I might faint"
    ]
    
    for query in high_queries:
        assert calculate_priority(query) == QueryPriority.HIGH

def test_calculate_priority_medium():
    # Test medium priority detection
    medium_queries = [
        "I've had a persistent cough for a week",
        "I'm experiencing ongoing fatigue",
        "I have chronic back pain that's getting worse",
        "I'm feeling anxious and stressed all the time",
        "I've been having trouble sleeping for weeks"
    ]
    
    for query in medium_queries:
        assert calculate_priority(query) == QueryPriority.MEDIUM

def test_calculate_priority_low():
    # Test low priority detection
    low_queries = [
        "What vitamins should I take for general health?",
        "Can you recommend exercises for better posture?",
        "I'd like information about seasonal allergies",
        "What's the best way to maintain dental health?",
        "How often should I get a physical examination?"
    ]
    
    for query in low_queries:
        assert calculate_priority(query) == QueryPriority.LOW

# Test safety score calculation
def test_calculate_safety_score_high():
    # Test high safety concern detection
    high_concern_queries = [
        "I've been thinking about suicide and have a plan",
        "I want to hurt myself and end it all",
        "I took an overdose of my medication",
        "I'm having thoughts of harming my family",
        "I'm in a violent relationship and fear for my life"
    ]
    
    for query in high_concern_queries:
        score = calculate_safety_score(query)
        assert score > 0.6, f"Expected high safety score (>0.6) for '{query}', got {score}"

def test_calculate_safety_score_medium():
    # Test medium safety concern detection
    medium_concern_queries = [
        "I sometimes think about what it would be like if I wasn't here",
        "I'm feeling very depressed and hopeless",
        "My partner gets angry and breaks things sometimes",
        "I've been drinking more alcohol than usual to cope",
        "I'm having dark thoughts but wouldn't act on them"
    ]
    
    for query in medium_concern_queries:
        score = calculate_safety_score(query)
        assert 0.2 < score < 0.6, f"Expected medium safety score (0.2-0.6) for '{query}', got {score}"

def test_calculate_safety_score_low():
    # Test low safety concern detection
    low_concern_queries = [
        "I have a mild headache",
        "My allergies are acting up",
        "I'm wondering if I should change my diet",
        "What exercises are good for back pain?",
        "How can I improve my sleep habits?"
    ]
    
    for query in low_concern_queries:
        score = calculate_safety_score(query)
        assert score <= 0.2, f"Expected low safety score (<=0.2) for '{query}', got {score}"

# Test escalation logic
def test_should_escalate():
    # Test cases that should be escalated
    escalation_cases = [
        "I'm having chest pain and can't breathe",
        "I've taken all my pills and want to die",
        "I'm thinking of hurting myself and have a plan",
        "I'm bleeding heavily and feel dizzy",
        "I think I'm having a stroke"
    ]
    
    for case in escalation_cases:
        assert should_escalate(case) == True, f"Expected escalation for '{case}'"

def test_should_not_escalate():
    # Test cases that should not be escalated
    non_escalation_cases = [
        "I have a mild cold",
        "What's the best vitamin for immune support?",
        "I've been feeling tired lately",
        "How can I improve my diet?",
        "I have occasional joint pain"
    ]
    
    for case in non_escalation_cases:
        assert should_escalate(case) == False, f"Expected no escalation for '{case}'"