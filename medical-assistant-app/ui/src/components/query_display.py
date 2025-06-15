import streamlit as st
from typing import Dict, Any, List, Optional
import requests

def display_query_card(query: Dict[str, Any], api_url: str, show_review: bool = True):
    """Display a patient query in a card format
    
    Args:
        query: Query data dictionary
        api_url: Base API URL
        show_review: Whether to show the review if available
    """
    # Create a card-like container
    with st.container():
        # Add a border and padding with CSS
        st.markdown("""
        <style>
        .query-card {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #f9f9f9;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="query-card">', unsafe_allow_html=True)
        
        # Query content and metadata
        st.subheader(f"Query ID: {query['id']}")
        st.write(f"**Status:** {query['status']}")
        st.write(f"**Priority:** {query['priority']}")
        st.write(f"**Submitted:** {query['created_at']}")
        
        # Query content
        st.markdown("**Query:**")
        st.write(query['content'])
        
        # Get and display files if any
        try:
            files_response = requests.get(f"{api_url}/file/{query['id']}")
            if files_response.status_code == 200:
                files = files_response.json()["files"]
                if files:
                    st.markdown("**Attached Files:**")
                    for file in files:
                        st.write(f"- {file['filename']} ({file['file_type']}, {file['file_size']} bytes)")
        except Exception as e:
            st.warning(f"Could not retrieve files: {str(e)}")
        
        # Get and display review if available and requested
        if show_review and (query['status'] == "reviewed" or query['status'] == "completed"):
            try:
                review_response = requests.get(f"{api_url}/review/{query['id']}")
                if review_response.status_code == 200:
                    review = review_response.json()
                    st.markdown("---")
                    st.markdown("**Doctor's Response:**")
                    st.write(review["content"])
                    st.write(f"*Reviewed by Doctor ID: {review['doctor_id']}*")
            except Exception as e:
                st.warning(f"Could not retrieve review: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

def display_query_list(queries: List[Dict[str, Any]], api_url: str, show_reviews: bool = True):
    """Display a list of patient queries
    
    Args:
        queries: List of query data dictionaries
        api_url: Base API URL
        show_reviews: Whether to show reviews if available
    """
    if not queries:
        st.info("No queries found.")
        return
    
    for query in queries:
        display_query_card(query, api_url, show_reviews)

def display_review_form(query_id: int, doctor_id: int, api_url: str, on_submit=None):
    """Display a form for doctors to review a query
    
    Args:
        query_id: ID of the query to review
        doctor_id: ID of the doctor performing the review
        api_url: Base API URL
        on_submit: Optional callback function to execute after successful submission
    """
    with st.form(f"review_form_{query_id}"):
        st.write("**Your Review:**")
        review_text = st.text_area("Response to patient:", height=150)
        approved = st.checkbox("Approve AI suggestion with modifications")
        notes = st.text_area("Internal notes (not shared with patient):", height=100)
        
        submitted = st.form_submit_button("Submit Review")
        
        if submitted and review_text:
            # Submit review to API
            try:
                review_response = requests.post(
                    f"{api_url}/review/{query_id}",
                    json={
                        "doctor_id": doctor_id,
                        "content": review_text,
                        "approved": approved,
                        "notes": notes
                    }
                )
                
                if review_response.status_code == 201:
                    st.success("Review submitted successfully!")
                    if on_submit:
                        on_submit()
                else:
                    st.error(f"Error submitting review: {review_response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")