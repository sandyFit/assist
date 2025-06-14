import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8001/api")
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8001")

def show_welcome_ui():
    st.title("Welcome to the Medical AI Assistant")
    st.write("""
        Having trouble explaining your symptoms? Assist helps you turn what you're feeling into clear, doctor-friendly questions — so you get the right care, faster. All advice is reviewed by physicians to keep you safe.
        
    
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
