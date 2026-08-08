import os
import streamlit as st
import requests
import time
import uuid

# Page setup
st.set_page_config(
    page_title="Workspace",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Initialize Session States
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed" not in st.session_state:
    st.session_state.indexed = False

# Sidebar: Document Management
with st.sidebar:
    st.title("📄 Documents")
    st.caption("Upload files to context-ground your chat.")
    
    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, TXT, CSV, or MD",
        type=["pdf", "docx", "txt", "csv", "md"]
    )

    if st.button("Process Document", use_container_width=True) and uploaded_file:
        # Use st.status to dynamically display step-by-step processing
        with st.status("Processing Document...", expanded=True) as status:
            try:
                # Step 1: Uploading File
                status.write("📤 **Step 1/4:** Uploading document to server...")
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                data = {"session_id": st.session_state.session_id}
                
                # Request backend to process document
                res = requests.post(f"{API_URL}/upload", files=files, data=data)
                
                if res.status_code == 200:
                    res_data = res.json()
                    chunks_count = res_data.get("chunks_created", "N/A")
                    
                    # Step 2: Document Splitting
                    status.write(f"✂️ **Step 2/4:** Extracting text and splitting into chunks... (`{chunks_count}` chunks created)")
                    time.sleep(0.3)
                    
                    # Step 3: Embeddings Generation
                    status.write("🧠 **Step 3/4:** Generating dense vector embeddings...")
                    time.sleep(0.3)
                    
                    # Step 4: Indexing Vector Database
                    status.write("💾 **Step 4/4:** Storing vectors and preparing retrieval index...")
                    time.sleep(0.3)
                    
                    status.update(label="Document Indexing Complete!", state="complete", expanded=False)
                    st.success(f"Successfully indexed **{res_data.get('filename', uploaded_file.name)}**!")
                    st.session_state.indexed = True
                else:
                    status.update(label="Document Processing Failed!", state="error")
                    st.error("Failed to index document. Check backend logs.")
            
            except Exception as e:
                status.update(label="Connection Error!", state="error")
                st.error(f"Error reaching server: {e}")

    st.divider()
    
    if st.button("Clear Chat & Session", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.indexed = False
        st.rerun()

# Main Workspace Header
st.title("Workspace")
st.caption("Ask questions about your uploaded documents.")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Re-render sources if they exist in the message history
        if "sources" in message and message["sources"]:
            with st.expander("🔍 Retrieved Context Sources"):
                st.json(message["sources"])

# Bottom Chat Input
if user_query := st.chat_input("Ask anything about your uploaded doc..."):
    if not st.session_state.indexed:
        st.warning("Please upload and process a document in the left sidebar first.")
    else:
        # Display user message immediately
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Generate Assistant response with retrieval step visibility
        with st.chat_message("assistant"):
            with st.status("Retrieving context & generating answer...", expanded=True) as query_status:
                try:
                    query_status.write("🔎 **Step 1/2:** Searching vector store for top matching context chunks...")
                    
                    res = requests.post(
                        f"{API_URL}/query",
                        json={"session_id": st.session_state.session_id, "query": user_query}
                    )
                    
                    if res.status_code == 200:
                        payload = res.json()
                        answer = payload.get("answer", "No answer found.")
                        sources = payload.get("sources", [])
                        
                        query_status.write("🤖 **Step 2/2:** Generating answer using retrieved context...")
                        query_status.update(label="Answer generated!", state="complete", expanded=False)
                        
                        st.markdown(answer)
                        
                        # Display sources if available
                        if sources:
                            with st.expander("🔍 Retrieved Context Sources"):
                                st.json(sources)
                        
                        # Store in history
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": answer,
                            "sources": sources
                        })
                    else:
                        query_status.update(label="Query Failed!", state="error")
                        st.error("Error retrieving answer from session database.")
                
                except Exception as e:
                    query_status.update(label="Connection Error!", state="error")
                    st.error(f"Could not connect to backend: {e}")