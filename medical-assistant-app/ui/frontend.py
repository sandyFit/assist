import streamlit as st
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8001")
API_URL = f"http://{API_HOST}:{API_PORT}/api"

# App configuration
st.set_page_config(
    page_title="Medical AI Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Session state initialization
if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "patient_id" not in st.session_state:
    st.session_state.patient_id = None

if "doctor_id" not in st.session_state:
    st.session_state.doctor_id = None

# Sidebar for role selection and login
with st.sidebar:
    st.title("Medical AI Assistant")
    st.subheader("Demo Application")
    
    # Role selection
    role = st.radio("Select your role:", ["Patient", "Doctor"])
    
    # Login form
    with st.form("login_form"):
        if role == "Patient":
            patient_id = st.text_input("Patient ID", value="1")
            patient_name = st.text_input("Name", value="Demo Patient")
            patient_email = st.text_input("Email", value="patient@demo.com")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                st.session_state.user_role = "patient"
                st.session_state.patient_id = int(patient_id)  # Convert to int
                st.success(f"Logged in as Patient: {patient_name}")
                st.rerun()
        else:
            doctor_id = st.text_input("Doctor ID", value="1")
            doctor_name = st.text_input("Name", value="Dr. Demo")
            doctor_specialty = st.text_input("Specialty", value="General Medicine")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                st.session_state.user_role = "doctor"
                st.session_state.doctor_id = int(doctor_id)  # Convert to int
                st.success(f"Logged in as Doctor: {doctor_name}")
                st.rerun()
    
    # Logout button
    if st.session_state.user_role:
        if st.button("Logout"):
            st.session_state.user_role = None
            st.session_state.patient_id = None
            st.session_state.doctor_id = None
            st.rerun()

# Main content based on role
if st.session_state.user_role == "patient":
    # Patient interface
    st.title("Patient Portal")
    
    # Tabs for different functions
    tab1, tab2, tab3 = st.tabs(["Submit Query", "My Queries", "Help"])
    
    with tab1:
        st.header("Submit a Medical Query")
        st.write("Please describe your medical question or concern below. A doctor will review your query and provide a response.")
        
        with st.form("query_form"):
            query_text = st.text_area("Your medical question:", height=150)
            
            # File upload
            uploaded_file = st.file_uploader("Upload relevant medical documents (optional)", 
                                           type=["pdf", "jpg", "jpeg", "png", "txt"])
            
            submitted = st.form_submit_button("Submit Query")
            
            if submitted and query_text:
                # Submit query to API
                try:
                    # Create query
                    query_response = requests.post(
                        f"{API_URL}/query/",
                        json={
                            "patient_id": st.session_state.patient_id,
                            "content": query_text
                        }
                    )
                    
                    if query_response.status_code == 201:
                        query_data = query_response.json()
                        query_id = query_data["id"]
                        
                        # Upload file if provided
                        if uploaded_file:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                            file_response = requests.post(
                                f"{API_URL}/file/{query_id}/upload",
                                files=files
                            )
                            
                            if file_response.status_code != 201:
                                st.error(f"Error uploading file: {file_response.text}")
                        
                        st.success("Your query has been submitted successfully! A doctor will review it soon.")
                        st.info(f"Query ID: {query_id} | Status: {query_data['status']} | Priority: {query_data['priority']}")
                    else:
                        st.error(f"Error submitting query: {query_response.status_code} - {query_response.text}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.error(f"API URL: {API_URL}/query/")
    
    with tab2:
        st.header("My Queries")
        st.write("View the status and responses to your previous queries.")
        
        # Refresh button
        if st.button("Refresh Queries"):
            st.rerun()
        
        # Get queries from API
        try:
            response = requests.get(
                f"{API_URL}/query/",
                params={"patient_id": st.session_state.patient_id}
            )
            
            if response.status_code == 200:
                queries = response.json()["queries"]
                
                if not queries:
                    st.info("You haven't submitted any queries yet.")
                else:
                    for query in queries:
                        with st.expander(f"Query: {query['content'][:50]}... (Status: {query['status']})"):
                            st.write(f"**Full Query:** {query['content']}")
                            st.write(f"**Status:** {query['status']}")
                            st.write(f"**Priority:** {query['priority']}")
                            st.write(f"**Submitted:** {query['created_at']}")
                            
                            # Get review if available
                            if query['status'] == "reviewed" or query['status'] == "completed":
                                try:
                                    review_response = requests.get(f"{API_URL}/review/{query['id']}")
                                    if review_response.status_code == 200:
                                        review = review_response.json()
                                        st.write("---")
                                        st.write("**Doctor's Response:**")
                                        st.write(review["content"])
                                        st.write(f"*Reviewed by Doctor ID: {review['doctor_id']}*")
                                except:
                                    st.warning("Could not retrieve doctor's response.")
            else:
                st.error(f"Error retrieving queries: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab3:
        st.header("Help & Information")
        st.write("**How to use the Medical AI Assistant:**")
        st.write("""
        1. **Submit a Query**: Describe your medical question or concern in detail. You can also upload relevant medical documents.
        2. **View Responses**: Check the 'My Queries' tab to see the status of your queries and doctor responses.
        3. **Priority System**: Queries are prioritized based on urgency. Urgent medical concerns receive faster attention.
        """)
        
        st.warning("**Important**: This is a demo application. In a medical emergency, please call emergency services immediately.")

elif st.session_state.user_role == "doctor":
    # Doctor interface
    st.title("Doctor Portal")
    
    # Tabs for different functions
    tab1, tab2, tab3 = st.tabs(["Review Queries", "Completed Reviews", "Debug"])
    
    with tab1:
        st.header("Queries Awaiting Review")
        st.write("Review patient queries and AI-generated suggestions.")
        
        # Refresh button
        if st.button("Refresh Queries"):
            st.rerun()
        
        # Debug: Show API call being made
        st.write(f"🔍 **Debug**: Fetching from `{API_URL}/query/?status=awaiting_review`")
        
        # Get queries awaiting review
        try:
            response = requests.get(
                f"{API_URL}/query/",
                params={"status": "awaiting_review"}
            )
            
            st.write(f"**API Response Status**: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                queries = data["queries"]
                total = data["total"]
                
                st.write(f"**Total awaiting review**: {total}")
                
                if not queries:
                    st.info("No queries awaiting review.")
                    
                    # Show all queries for debugging
                    st.write("---")
                    st.write("**Debug: All queries in system:**")
                    all_response = requests.get(f"{API_URL}/query/")
                    if all_response.status_code == 200:
                        all_queries = all_response.json()["queries"]
                        for q in all_queries:
                            st.write(f"- Query {q['id']}: Status = {q['status']}, Priority = {q['priority']}")
                else:
                    for query in queries:
                        with st.expander(f"Query ID {query['id']}: {query['content'][:50]}... (Priority: {query['priority']})"):
                            st.write(f"**Patient Query:** {query['content']}")
                            st.write(f"**Priority:** {query['priority']}")
                            st.write(f"**Submitted:** {query['created_at']}")
                            
                            # Simulate AI suggestion for demo
                            st.write("---")
                            st.write("**AI-Generated Suggestion:**")
                            st.info("Based on the patient's symptoms, I recommend the following approach: [This is a simulated AI response for demo purposes]")
                            
                            # Review form
                            with st.form(f"review_form_{query['id']}"):
                                st.write("**Your Review:**")
                                review_text = st.text_area("Response to patient:", height=150, key=f"review_text_{query['id']}")
                                approved = st.checkbox("Approve AI suggestion with modifications", key=f"approved_{query['id']}")
                                notes = st.text_area("Internal notes (not shared with patient):", height=100, key=f"notes_{query['id']}")
                                
                                submitted = st.form_submit_button("Submit Review")
                                
                                if submitted and review_text:
                                    # Submit review to API
                                    try:
                                        review_response = requests.post(
                                            f"{API_URL}/review/{query['id']}",
                                            json={
                                                "doctor_id": st.session_state.doctor_id,
                                                "content": review_text,
                                                "approved": approved,
                                                "notes": notes
                                            }
                                        )
                                        
                                        if review_response.status_code == 201:
                                            st.success("Review submitted successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"Error submitting review: {review_response.status_code} - {review_response.text}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
            else:
                st.error(f"Error retrieving queries: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.header("Completed Reviews")
        st.write("View your previously completed reviews.")
        
        # Get completed reviews
        try:
            response = requests.get(
                f"{API_URL}/review/",
                params={"doctor_id": st.session_state.doctor_id}
            )
            
            if response.status_code == 200:
                reviews = response.json()["reviews"]
                
                if not reviews:
                    st.info("You haven't completed any reviews yet.")
                else:
                    for review in reviews:
                        # Get query details
                        query_response = requests.get(f"{API_URL}/query/{review['query_id']}")
                        if query_response.status_code == 200:
                            query = query_response.json()
                            
                            with st.expander(f"Review for Query ID {review['query_id']} (Completed: {review['created_at']})"):
                                st.write(f"**Patient Query:** {query['content']}")
                                st.write("---")
                                st.write("**Your Response:**")
                                st.write(review["content"])
                                st.write(f"**Approved AI Suggestion:** {'Yes' if review['approved'] else 'No'}")
                                if review["notes"]:
                                    st.write("**Internal Notes:**")
                                    st.write(review["notes"])
            else:
                st.error(f"Error retrieving reviews: {response.text}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab3:
        st.header("Debug Information")
        st.write("System information for troubleshooting.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("API Status")
            try:
                health_response = requests.get(f"http://{API_HOST}:{API_PORT}/health")
                if health_response.status_code == 200:
                    st.success("✅ API is responding")
                    st.json(health_response.json())
                else:
                    st.error(f"❌ API health check failed: {health_response.status_code}")
            except Exception as e:
                st.error(f"❌ Cannot connect to API: {str(e)}")
        
        with col2:
            st.subheader("Session State")
            st.json({
                "user_role": st.session_state.user_role,
                "patient_id": st.session_state.patient_id,
                "doctor_id": st.session_state.doctor_id,
                "api_url": API_URL
            })
        
        st.subheader("All Queries in System")
        if st.button("Fetch All Queries"):
            try:
                all_response = requests.get(f"{API_URL}/query/")
                if all_response.status_code == 200:
                    all_data = all_response.json()
                    st.json(all_data)
                else:
                    st.error(f"Error: {all_response.status_code} - {all_response.text}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

else:
    # Welcome screen
    st.title("Welcome to the Medical AI Assistant")
    st.write("""
    This demo application showcases a medical AI assistant with human oversight.
    
    **Key Features:**
    - Submit medical queries and receive doctor-reviewed responses
    - Upload relevant medical documents for context
    - AI-assisted suggestions for medical professionals
    - Complete doctor review of all AI-generated content
    
    Please select your role in the sidebar to get started.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("For Patients")
        st.write("""
        - Submit medical questions
        - Upload relevant documents
        - Receive doctor-reviewed responses
        - Track status of your queries
        """)
    
    with col2:
        st.subheader("For Doctors")
        st.write("""
        - Review patient queries
        - Evaluate AI-generated suggestions
        - Provide expert medical guidance
        - Track your completed reviews
        """)
    
    st.info("This is a demo application for a hackathon. It is not intended for actual medical use.")
