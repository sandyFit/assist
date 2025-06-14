# AI Prompting Strategy

## Overview

This document outlines the prompting strategy used for the Medical AI Assistant application. Effective prompting is crucial for generating safe, accurate, and helpful medical information while ensuring human oversight remains central to the system.

## System Prompt Design

### Core Components

Our system prompt for the medical AI assistant contains the following key elements:

1. **Role Definition**: Clearly defines the AI as a medical information assistant that works alongside healthcare professionals, not as a replacement.

2. **Scope Limitations**: Explicitly states what the AI can and cannot do, emphasizing that all outputs require doctor review.

3. **Safety Guidelines**: Includes specific instructions for handling potentially dangerous or urgent medical situations.

4. **Response Format**: Structures AI responses in a consistent format that separates observations, reasoning, and suggestions.

5. **Confidence Indicators**: Requires the AI to express uncertainty when appropriate and provide confidence levels for suggestions.

### Sample System Prompt

```
You are a Medical Information Assistant working within a healthcare system where all your outputs are reviewed by licensed medical professionals before being shared with patients. Your role is to help analyze medical queries and provide informational suggestions, not to diagnose or prescribe.

Guidelines:
1. Always indicate that your suggestions require doctor review
2. Express appropriate levels of certainty/uncertainty
3. For urgent medical concerns, emphasize the need for immediate medical attention
4. Structure your response with clear sections: Observations, Reasoning, and Suggestions
5. Provide a confidence score (0-100%) for your suggestions
6. Never recommend specific medications, dosages, or treatments
7. Always consider patient safety as the highest priority

Format your response as follows:

OBSERVATIONS:
[Key information from the patient's query or uploaded documents]

REASONING:
[Your analysis of the information, including differential considerations]

SUGGESTIONS (Confidence: X%):
[Informational suggestions that will require doctor review]

SAFETY NOTES:
[Any safety concerns or urgency indicators]
```

## Query-Specific Prompting

### Basic Patient Queries

For standard patient queries without attached files, we use a focused prompt that includes:

1. The system prompt described above
2. The patient's query verbatim
3. Any relevant patient information from their profile (age, medical history)
4. Instructions to prioritize the query (urgent, high, medium, low)

### Document-Enhanced Queries

When patients upload medical documents, we enhance the prompt with:

1. Extracted text from the documents
2. Document type identification
3. Instructions to correlate document information with the patient's query
4. Guidance on handling potentially conflicting information

## Safety Mechanisms in Prompting

### Keyword Triggers

Certain medical keywords in patient queries trigger additional prompt components:

1. **Emergency Keywords** (chest pain, difficulty breathing, etc.): Add explicit instructions to emphasize immediate medical attention

2. **Mental Health Keywords** (suicide, self-harm, etc.): Include specific mental health safety protocols in the prompt

3. **Medication Keywords**: Add reminders about not recommending specific medications or dosages

### Confidence Calibration

The prompt instructs the AI to:

1. Provide a numerical confidence score (0-100%)
2. Use calibrated language that matches the confidence level
3. List alternative possibilities when confidence is low
4. Explicitly state limitations of the analysis

## Continuous Improvement

### Feedback Integration

Doctor reviews of AI suggestions are used to improve prompting through:

1. Identifying patterns in rejected or heavily modified suggestions
2. Refining keyword triggers based on missed urgency assessments
3. Adjusting confidence calibration based on actual accuracy

### A/B Testing

We systematically test prompt variations to optimize for:

1. Safety (highest priority)
2. Accuracy of medical information
3. Helpfulness of suggestions
4. Appropriate expression of uncertainty

## Implementation Notes

### Technical Integration

The prompting system is implemented in the `app/llm/suggestion.py` module with the following components:

1. Base system prompt template
2. Query analysis and keyword detection
3. Dynamic prompt construction based on query content and attached files
4. Response parsing to extract structured information

### Limitations

Current limitations of our prompting approach include:

1. Limited personalization based on patient history
2. No integration with medical knowledge databases for real-time fact-checking
3. English-language focus without multilingual support

These limitations would need to be addressed in a production implementation.