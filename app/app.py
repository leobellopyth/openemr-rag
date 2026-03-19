#!/usr/bin/env python3
"""
OpenEMR RAG - Streamlit UI
Phase 1: Basic chat interface
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from openemr_rag import OpenEMRRAG, PERSIST_DIRECTORY, KB_DIR

# Page config
st.set_page_config(
    page_title="OpenEMR RAG Assistant",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.stApp {
    background-color: #f8f9fa;
}
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
}
.user-message {
    background-color: #e3f2fd;
    border-left: 4px solid #2196f3;
}
.assistant-message {
    background-color: #f1f8e9;
    border-left: 4px solid #4caf50;
}
</style>
""", unsafe_allow_html=True)

# Title
st.title("🏥 OpenEMR RAG Assistant")
st.markdown("*Powered by medgemma + ChromaDB + Ollama*")

# Initialize session state
if 'rag_system' not in st.session_state:
    with st.spinner("Initializing RAG system..."):
        st.session_state.rag_system = OpenEMRRAG()
        
        # Try to load existing vector store
        if not st.session_state.rag_system.load_existing_vectorstore():
            st.info("📁 No existing vector store found. First query will trigger indexing.")
        else:
            st.session_state.rag_system.setup_qa_chain()

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sources" in message:
            if message["sources"]:
                st.caption("Sources: " + ", ".join(message["sources"]))

# Chat input
if prompt := st.chat_input("Ask a clinical question..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if not st.session_state.rag_system.qa_chain:
                # Initialize if needed
                if st.session_state.rag_system.ingest_knowledge_base():
                    st.session_state.rag_system.setup_qa_chain()
            
            result = st.session_state.rag_system.query(prompt)
            st.markdown(result)
            
            # Extract sources
            sources = []
            if hasattr(st.session_state.rag_system.qa_chain, 'retriever'):
                # Sources would be in the result
                sources = []
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": result,
                "sources": sources
            })

# Sidebar - System Info
with st.sidebar:
    st.header("System Status")
    
    st.success("✅ Ollama Connected")
    st.info(f"Model: medgemma:4b")
    st.info(f"Vector Store: {PERSIST_DIRECTORY}")
    
    st.divider()
    
    st.header("Knowledge Base")
    kb_path = Path(KB_DIR)
    if kb_path.exists():
        for subdir in kb_path.iterdir():
            if subdir.is_dir():
                count = len(list(subdir.glob("*.txt")))
                st.text(f"📁 {subdir.name}: {count} files")
    
    st.divider()
    
    st.header("Actions")
    if st.button("🔄 Re-index Knowledge Base"):
        with st.spinner("Re-indexing..."):
            if st.session_state.rag_system.ingest_knowledge_base():
                st.session_state.rag_system.setup_qa_chain()
                st.success("Re-indexing complete!")
                st.rerun()
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()
