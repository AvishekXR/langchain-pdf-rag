import streamlit as st
import tempfile
import os
import hashlib
import asyncio

# --- Asyncio 
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Local imports
from main import setup_rag_pipeline, ask_question

# Streamlit UI
st.title("📄 PDF Question Answering with RAG")
st.write("Upload a PDF and ask questions about its content.")

# Initialize session state
if 'qa_chain' not in st.session_state:
    st.session_state.qa_chain = None
if 'uploaded_file_id' not in st.session_state:
    st.session_state.uploaded_file_id = None

# PDF upload
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

# Process uploaded PDF only if a new file is uploaded
if uploaded_file is not None:
    # Generate unique hash for uploaded content
    file_content = uploaded_file.read()
    file_id = hashlib.md5(file_content).hexdigest()
    uploaded_file.seek(0)

    # Process only if it's a new file
    if file_id != st.session_state.uploaded_file_id:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(file_content)
            tmp_file_path = tmp_file.name

        with st.spinner("🔄 Processing PDF..."):
            try:
                st.session_state.qa_chain = setup_rag_pipeline(tmp_file_path)
                st.session_state.uploaded_file_id = file_id
                st.success("✅ PDF processed successfully!")
            except Exception as e:
                st.error(f"❌ Error processing PDF: {str(e)}")
                st.session_state.qa_chain = None
                st.session_state.uploaded_file_id = None
            finally:
                os.unlink(tmp_file_path)
else:
    st.session_state.qa_chain = None
    st.session_state.uploaded_file_id = None

# Question input
if st.session_state.qa_chain:
    question = st.text_input("❓ Ask a question about the document:")
    if question:
        with st.spinner("🤖 Generating answer..."):
            try:
                answer, sources = ask_question(st.session_state.qa_chain, question)
                st.markdown("### ✅ Answer:")
                st.write(answer)

                if sources:
                    st.markdown("### 📚 Sources:")
                    for i, doc in enumerate(sources, 1):
                        page = doc.metadata.get("page", "N/A")
                        preview = doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                        st.markdown(f"**Source {i} (Page {page + 1}):**")
                        st.write(preview)
                else:
                    st.warning("No sources found.")
            except Exception as e:
                st.error(f"❌ Error answering question: {str(e)}")
else:
    st.info("📥")
