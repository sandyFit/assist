# UI package initialization
# This file ensures the ui directory is recognized as a Python package
import streamlit as st
from src.patient_page import show_patient_ui
from src.doctor_page import show_doctor_ui
from src.welcome_page import show_welcome_ui


# Hide default navigation
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

# Main view
if st.session_state.user_role == "patient":
    show_patient_ui()
elif st.session_state.user_role == "doctor":
    show_doctor_ui()
else:
    show_welcome_ui()
