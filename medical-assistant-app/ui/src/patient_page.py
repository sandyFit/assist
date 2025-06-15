import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8001/api")
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8001")

def show_patient_ui():
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
                                           type=["pdf", "txt"])
            
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
                    # st.write("🟢 Query response:", query_response.status_code)
                    # st.write("🔎 Query response content:", query_response.text)

                    if query_response.status_code == 201:
                        query_data = query_response.json()
                        query_id = query_data["id"]
                        
                        # Upload file if provided
                        if uploaded_file:
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                            # Fixed URL - remove extra 'file' prefix
                            with st.spinner("📤 Uploading file and extracting text..."):
                                file_response = requests.post(
                                    f"{API_URL}/file/{query_id}/upload",
                                    files=files
                                )

                            
                            # st.write(f"🟢 File upload response: {file_response.status_code}")
                            # st.write(f"🔎 File upload content: {file_response.text}")

                            if file_response.status_code == 201:
                                file_data = file_response.json()
                                extracted_text = file_data.get("text_content", "")
                                if extracted_text:
                                    st.success("✅ Text extracted from uploaded file:")
                                    st.code(extracted_text[:1000], language="text")
                                else:
                                    st.info("File uploaded successfully, but no text content was extracted.")
                                
                                # st.json(file_data)
                            else:
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
                            
                            # Show uploaded files if any
                            try:
                                files_response = requests.get(f"{API_URL}/file/{query['id']}")
                                if files_response.status_code == 200:
                                    files_data = files_response.json()
                                    if files_data["files"]:
                                        st.write("**Uploaded Files:**")
                                        for file_info in files_data["files"]:
                                            st.write(f"- {file_info['filename']} ({file_info['file_type']})")
                                            if file_info.get("text_content"):
                                                st.write("  **Extracted Text:**")
                                                st.code(file_info["text_content"][:500], language="text")
                            except:
                                pass  # Ignore file retrieval errors
                            
                            # Get review if available
                            if query['status'] == "reviewed" or query['status'] == "completed":
                                try:
                                    review_response = requests.get(f"{API_URL}/review/{query['id']}")
                                    if review_response.status_code == 200:
                                        review = review_response.json()
                                        st.write("---")
                                        st.subheader("💡 Final Suggestion from Doctor")
                                        st.success(review["content"])
                                        st.caption(f"Reviewed by Doctor ID: {review['doctor_id']}")

                                        if review["approved"]:
                                            st.info("✅ This suggestion was approved by the doctor.")
                                        else:
                                            st.warning("✏️ This is a modified version of the AI suggestion.")

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
