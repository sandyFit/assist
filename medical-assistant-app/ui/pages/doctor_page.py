import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8001/api")
API_HOST = os.getenv("API_HOST", "localhost")
API_PORT = os.getenv("API_PORT", "8001")

def show_doctor_ui():
    st.title("Doctor Portal")
    tab1, tab2, tab3 = st.tabs(["Review Queries", "Completed Reviews", "Debug"])

    with tab1:
        st.header("Queries Awaiting Review")
        st.write("Review patient queries and provide medical advice.")

        if st.button("Refresh Queries"):
            st.rerun()

        try:
            response = requests.get(f"{API_URL}/query/", params={"status": "awaiting_review"})
            if response.status_code == 200:
                data = response.json()
                queries = data["queries"]
                total = data["total"]
                st.write(f"**Total queries awaiting review**: {total}")

                if not queries:
                    st.info("No queries awaiting review.")
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

                            try:
                                files_response = requests.get(f"{API_URL}/file/{query['id']}")
                                if files_response.status_code == 200:
                                    files_data = files_response.json()
                                    if files_data["files"]:
                                        st.write("**Uploaded Files:**")
                                        for file_info in files_data["files"]:
                                            st.write(f"- {file_info['filename']} ({file_info['file_type']})")
                                            if file_info.get("text_content"):
                                                with st.expander(f"View extracted text from {file_info['filename']}"):
                                                    st.code(file_info["text_content"], language="text")
                            except:
                                pass

                            st.write("---")
                            st.subheader("💡 AI Suggestion (Placeholder)")
                            
                            # Placeholder suggestion text
                            placeholder_suggestion = """This is a placeholder for AI-generated medical suggestions.
                            
In a production system, this would contain:
- Initial assessment based on symptoms
- Recommended diagnostic tests
- Potential treatment options
- Follow-up recommendations
- Red flags or urgent care indicators

Please provide your professional medical advice below."""

                            st.text_area("AI Suggestion (Placeholder):", value=placeholder_suggestion, height=120, disabled=True, key=f"ai_suggestion_display_{query['id']}")

                            st.info("ℹ️ AI suggestion feature is currently disabled. Please provide your medical advice directly.")

                            with st.form(f"review_form_{query['id']}"):
                                st.write("🩺 **Doctor Review**")
                                review_text = st.text_area("✍️ Edit and provide your medical advice:", value=placeholder_suggestion, height=150, key=f"review_text_{query['id']}")
                                approved = st.checkbox("✅ Approve and send to patient", key=f"approved_{query['id']}")

                                submit_review = st.form_submit_button("Submit Review")
                                if submit_review and review_text:
                                    review_payload = {
                                        "doctor_id": st.session_state.doctor_id,
                                        "content": review_text,
                                        "approved": approved
                                    }

                                    try:
                                        review_response = requests.post(f"{API_URL}/review/{query['id']}", json=review_payload)
                                        if review_response.status_code == 201:
                                            st.success("✅ Review submitted successfully!")
                                            st.rerun()
                                        else:
                                            st.error(f"❌ Error: {review_response.status_code} - {review_response.text}")
                                    except Exception as e:
                                        st.error(f"❌ Submission error: {str(e)}")
                                elif submit_review and not review_text:
                                    st.error("❌ Please provide your medical advice before submitting.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    with tab2:
        st.header("Completed Reviews")
        st.write("View your previously completed reviews.")

        try:
            response = requests.get(f"{API_URL}/review/", params={"doctor_id": st.session_state.doctor_id})
            if response.status_code == 200:
                reviews = response.json()["reviews"]
                if not reviews:
                    st.info("You haven't completed any reviews yet.")
                else:
                    for review in reviews:
                        query_response = requests.get(f"{API_URL}/query/{review['query_id']}")
                        if query_response.status_code == 200:
                            query = query_response.json()
                            with st.expander(f"Review for Query ID {review['query_id']} (Completed: {review['created_at']})"):
                                st.write(f"**Patient Query:** {query['content']}")
                                st.write("---")
                                st.write("**Your Response:**")
                                st.write(review["content"])
                                st.write(f"**Status:** {'Approved and sent to patient' if review['approved'] else 'Draft - not sent'}")
                                if review.get("notes"):
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
                "user_role": st.session_state.get("user_role", "unknown"),
                "patient_id": st.session_state.get("patient_id", None),
                "doctor_id": st.session_state.get("doctor_id", None),
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
