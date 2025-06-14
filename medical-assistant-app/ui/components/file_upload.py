import streamlit as st
import requests
from typing import Optional, List, Dict, Any

def file_uploader_component(api_url: str, query_id: Optional[int] = None):
    """Display a file uploader component
    
    Args:
        api_url: Base API URL
        query_id: Optional query ID to associate files with
    
    Returns:
        bool: True if file was uploaded successfully, False otherwise
    """
    st.subheader("Upload Medical Documents")
    st.write("Upload relevant medical documents to provide additional context for your query.")
    
    # File upload widget
    uploaded_file = st.file_uploader(
        "Choose a file", 
        type=["pdf", "jpg", "jpeg", "png", "txt", "csv", "doc", "docx"],
        help="Upload medical records, test results, or other relevant documents"
    )
    
    if uploaded_file is not None:
        # Display file info
        st.write(f"File: {uploaded_file.name} ({uploaded_file.type}, {uploaded_file.size} bytes)")
        
        # Upload button
        if st.button("Upload File"):
            if query_id is None:
                st.error("No query ID provided. Please submit your query first.")
                return False
            
            # Upload file to API
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                response = requests.post(
                    f"{api_url}/file/{query_id}/upload",
                    files=files
                )
                
                if response.status_code == 201:
                    st.success("File uploaded successfully!")
                    return True
                else:
                    st.error(f"Error uploading file: {response.text}")
                    return False
            except Exception as e:
                st.error(f"Error: {str(e)}")
                return False
    
    return False

def display_uploaded_files(api_url: str, query_id: int):
    """Display files uploaded for a specific query
    
    Args:
        api_url: Base API URL
        query_id: Query ID to get files for
    
    Returns:
        List[Dict[str, Any]]: List of file data dictionaries
    """
    try:
        response = requests.get(f"{api_url}/file/{query_id}")
        
        if response.status_code == 200:
            files = response.json()["files"]
            
            if files:
                st.subheader("Uploaded Files")
                
                for file in files:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{file['filename']}** ({file['file_type']}, {file['file_size']} bytes)")
                    
                    with col2:
                        # Delete button
                        if st.button(f"Delete", key=f"delete_{file['id']}"):
                            try:
                                delete_response = requests.delete(f"{api_url}/file/{file['id']}")
                                
                                if delete_response.status_code == 204:
                                    st.success("File deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error deleting file: {delete_response.text}")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
            
            return files
        else:
            st.error(f"Error retrieving files: {response.text}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    return []