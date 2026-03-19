#!/usr/bin/env python3
"""
OpenEMR RAG System
Enhanced with clinical decision support features
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "alibayram/medgemma:4b"
EMBEDDING_MODEL = "nomic-embed-text"
PERSIST_DIRECTORY = "vector_store/faiss_index"

# OpenEMR Configuration
OPENEMR_HOST = "16.58.52.89"
OPENEMR_API_PORT = 3001


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def cprint(text, color=""):
    """Print with color."""
    print(f"{color}{text}{Colors.ENDC}")


class OpenEMRAPI:
    """OpenEMR REST API client via chartprep backend."""
    
    def __init__(self, host=OPENEMR_HOST, port=OPENEMR_API_PORT):
        self.host = host
        self.port = port
        self.base_url = f"http://localhost:{port}"
        self._tunnel_process = None
        self.connected = False
    
    def start_ssh_tunnel(self):
        """Start SSH tunnel to OpenEMR backend."""
        import subprocess
        
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'ssh.exe'], 
                         stderr=subprocess.DEVNULL, timeout=2)
        except:
            pass
        
        try:
            self._tunnel_process = subprocess.Popen(
                ['ssh', '-i', 'C:\\Users\\leobe\\.ssh\\OpenEMRLeo.pem',
                 '-N', '-L', f'{self.port}:localhost:{self.port}',
                 f'ubuntu@{self.host}'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            import time
            time.sleep(2)
            self.connected = True
            return True
        except Exception as e:
            print(f"SSH tunnel failed: {e}")
            return False
    
    def stop_ssh_tunnel(self):
        """Stop SSH tunnel."""
        if self._tunnel_process:
            self._tunnel_process.terminate()
            self._tunnel_process = None
            self.connected = False
    
    def api_request(self, endpoint, method="GET", params=None, data=None):
        """Make API request."""
        try:
            response = requests.request(
                method,
                f"{self.base_url}/{endpoint}",
                params=params,
                json=data,
                timeout=30
            )
            return response
        except Exception as e:
            return None
    
    def get_patient_data(self, patient_id):
        """Get complete patient data."""
        response = self.api_request(f"api/patient/{patient_id}")
        if response and response.status_code == 200:
            return response.json()
        return None
    
    def get_patient_summary(self, patient_id):
        """Get brief patient summary for display."""
        data = self.get_patient_data(patient_id)
        if not data:
            return None
        
        name = data.get('name', {})
        dob = data.get("birthDate", "")
        if dob:
            dob = str(dob)[:10]  # Just YYYY-MM-DD
        
        return {
            "id": data.get("id"),
            "name": f"{name.get('given', '')} {name.get('family', '')}",
            "birthDate": dob,
            "gender": data.get("gender"),
            "conditions_count": len(data.get("conditions", [])),
            "medications_count": len(data.get("medications", [])),
            "allergies_count": len(data.get("allergies", [])),
            "latest_vitals": data.get("vitals", [{}])[0] if data.get("vitals") else {}
        }


class OpenEMRRAG:
    """RAG system with OpenEMR integration."""
    
    def __init__(self, model_name=MODEL_NAME, embedding_model=EMBEDDING_MODEL):
        cprint(f"\n{'='*60}", Colors.CYAN)
        cprint("  OpenEMR Clinical Decision Support System", Colors.CYAN + Colors.BOLD)
        cprint(f"  Powered by {model_name}", Colors.CYAN)
        cprint(f"{'='*60}\n", Colors.CYAN)
        
        self.llm = OllamaLLM(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.3,
            timeout=180
        )
        cprint("[OK] LLM initialized", Colors.GREEN)
        
        self.embeddings = OllamaEmbeddings(
            model=embedding_model,
            base_url=OLLAMA_BASE_URL
        )
        cprint("[OK] Embeddings ready", Colors.GREEN)
        
        self.vectorstore = None
        self.qa_chain = None
        self.openemr_api = OpenEMRAPI()
        
        if self.openemr_api.start_ssh_tunnel():
            cprint("[OK] Connected to OpenEMR", Colors.GREEN)
        else:
            cprint("[!] OpenEMR not connected (will use local KB only)", Colors.YELLOW)
        
        self.current_patient = None
        self.query_history = []
    
    def load_documents(self, directory):
        """Load documents from a directory."""
        from langchain_community.document_loaders import DirectoryLoader, TextLoader
        documents = []
        if not Path(directory).exists():
            return documents
        try:
            loader = DirectoryLoader(directory, glob="**/*.txt", loader_cls=TextLoader)
            documents.extend(loader.load())
        except Exception as e:
            print(f"Error: {e}")
        return documents
    
    def ingest_knowledge_base(self, kb_directory=Path("knowledge_base")):
        """Ingest knowledge base into vector store."""
        cprint(f"\nIngesting knowledge base...", Colors.YELLOW)
        
        all_documents = []
        for subdir in kb_directory.iterdir():
            if subdir.is_dir():
                docs = self.load_documents(subdir)
                all_documents.extend(docs)
                cprint(f"  {subdir.name}: {len(docs)} docs", Colors.BLUE)
        
        if not all_documents:
            cprint("  No documents found in knowledge_base/", Colors.RED)
            return False
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
            length_function=len
        )
        chunks = text_splitter.split_documents(all_documents)
        cprint(f"  Created {len(chunks)} chunks", Colors.BLUE)
        
        self.vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=self.embeddings
        )
        self.vectorstore.save_local(PERSIST_DIRECTORY)
        cprint(f"[OK] Vector store saved", Colors.GREEN)
        return True
    
    def load_existing_vectorstore(self):
        """Load existing vector store."""
        if Path(PERSIST_DIRECTORY).exists():
            try:
                self.vectorstore = FAISS.load_local(
                    PERSIST_DIRECTORY,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                cprint("[OK] Knowledge base loaded", Colors.GREEN)
                return True
            except Exception as e:
                print(f"Error: {e}")
        return False
    
    def setup_qa_chain(self):
        """Set up the QA chain."""
        if not self.vectorstore:
            cprint("[!] No vector store available", Colors.RED)
            return False
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a clinical decision support assistant. Use the provided context and patient data to give accurate, helpful responses.

Clinical Context:
{context}

If patient data is provided, consider:
- Current medications and allergies (avoid interactions)
- Diagnosed conditions
- Recent vitals
- Social determinants of health

Be concise but thorough. Flag critical concerns."""),
            ("human", "{question}")
        ])
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})
        
        self.qa_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
        )
        cprint("[OK] Ready for queries\n", Colors.GREEN)
        return True
    
    def query(self, question, patient_data=None):
        """Query the RAG system."""
        if not self.qa_chain:
            return "QA chain not ready."
        
        timestamp = datetime.now().strftime("%H:%M")
        self.query_history.append({"time": timestamp, "q": question})
        
        cprint(f"\n[{timestamp}] Query: {question[:60]}{'...' if len(question) > 60 else ''}", Colors.YELLOW)
        print("-" * 60)
        
        if patient_data:
            context_str = self._format_patient_context(patient_data)
            full_question = f"{question}\n\nPatient Data:\n{context_str}"
        else:
            full_question = question
        
        try:
            result = self.qa_chain.invoke(full_question)
            cprint(result, Colors.WHITE)
            return result
        except Exception as e:
            cprint(f"Error: {e}", Colors.RED)
            return str(e)
    
    def _format_patient_context(self, data):
        """Format patient data for context."""
        lines = []
        name = data.get('name', {})
        lines.append(f"Patient: {name.get('given', '')} {name.get('family', '')}")
        lines.append(f"Gender: {data.get('gender', 'Unknown')}")
        
        dob = data.get('birthDate', '')
        if dob:
            dob = str(dob)[:10]
        
        if data.get('conditions'):
            lines.append(f"\nDiagnoses ({len(data['conditions'])}):")
            for c in data['conditions'][:5]:
                lines.append(f"  - {c.get('title', 'Unknown')}")
        
        if data.get('medications'):
            lines.append(f"\nActive Medications ({len(data['medications'])}):")
            for m in data['medications'][:5]:
                lines.append(f"  - {m.get('drug', 'Unknown')} {m.get('dosage', '')}")
        
        if data.get('allergies'):
            lines.append(f"\nAllergies ({len(data['allergies'])}):")
            for a in data['allergies'][:3]:
                lines.append(f"  - {a.get('title', 'Unknown')}")
        
        if data.get('vitals') and len(data['vitals']) > 0:
            v = data['vitals'][0]
            lines.append(f"\nLatest Vitals:")
            lines.append(f"  BP: {v.get('bps', '-')}/{v.get('bpd', '-')}")
            lines.append(f"  HR: {v.get('pulse', '-')}")
            lines.append(f"  SpO2: {v.get('oxygen_saturation', '-')}%")
        
        return "\n".join(lines)
    
    def show_patient_summary(self, patient_id):
        """Show patient summary."""
        summary = self.openemr_api.get_patient_summary(patient_id)
        if not summary:
            cprint("[!] Patient not found", Colors.RED)
            return
        
        self.current_patient = patient_id
        
        cprint(f"\n{'='*50}", Colors.CYAN)
        cprint(f"  Patient Summary - #{patient_id}", Colors.CYAN + Colors.BOLD)
        cprint(f"{'='*50}", Colors.CYAN)
        cprint(f"  Name: {summary['name']}", Colors.WHITE)
        cprint(f"  DOB: {summary['birthDate']}", Colors.WHITE)
        cprint(f"  Gender: {summary['gender']}", Colors.WHITE)
        print()
        cprint(f"  Conditions: {summary['conditions_count']}", Colors.YELLOW)
        cprint(f"  Medications: {summary['medications_count']}", Colors.YELLOW)
        cprint(f"  Allergies: {summary['allergies_count']}", Colors.YELLOW)
        
        v = summary.get('latest_vitals', {})
        if v:
            cprint(f"\n  Latest Vitals:", Colors.YELLOW)
            cprint(f"    BP: {v.get('bps', '-')}/{v.get('bpd', '-')} mmHg", Colors.WHITE)
            cprint(f"    HR: {v.get('pulse', '-')} bpm", Colors.WHITE)
            cprint(f"    SpO2: {v.get('oxygen_saturation', '-')}%", Colors.WHITE)
        
        cprint(f"\n  Type '?' or 'help' for commands", Colors.BLUE)
        cprint(f"{'='*50}\n", Colors.CYAN)
    
    def quick_clinical_queries(self, patient_id):
        """Run quick clinical queries on patient."""
        patient_data = self.openemr_api.get_patient_data(patient_id)
        if not patient_data:
            cprint("[!] Patient not found", Colors.RED)
            return
        
        queries = [
            ("Medication Review", "Review these medications for any concerns, interactions, or optimization opportunities."),
            ("Vitals Analysis", "Analyze the vital signs. Are there any concerning trends or values?"),
            ("Risk Assessment", "Based on the patient data, what are the top 3 clinical concerns?"),
            ("Care Gaps", "What preventive care or chronic disease management gaps might exist?"),
        ]
        
        cprint(f"\n{'='*60}", Colors.CYAN)
        cprint("  Running Clinical Queries...", Colors.CYAN + Colors.BOLD)
        cprint(f"{'='*60}\n", Colors.CYAN)
        
        for title, question in queries:
            cprint(f"\n[{title}]", Colors.YELLOW + Colors.BOLD)
            self.query(question, patient_data)
            print()
    
    def interactive_mode(self):
        """Interactive query mode."""
        cprint("Commands:", Colors.BOLD)
        cprint("  ask <question>     - Query with clinical guidelines", Colors.BLUE)
        cprint("  patient <id>        - Load patient and show summary", Colors.BLUE)
        cprint("  analyze <id>       - Run automated clinical analysis", Colors.BLUE)
        cprint("  ?, help            - Show this help", Colors.BLUE)
        cprint("  history            - Show query history", Colors.BLUE)
        cprint("  quit               - Exit\n", Colors.BLUE)
        
        while True:
            try:
                user_input = input(f"{Colors.GREEN}> {Colors.ENDC}").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.openemr_api.stop_ssh_tunnel()
                    cprint("\nGoodbye!", Colors.CYAN)
                    break
                
                if user_input in ['?', 'help']:
                    continue
                
                if user_input.lower() == 'history':
                    cprint(f"\nQuery History ({len(self.query_history)} queries):", Colors.YELLOW)
                    for i, h in enumerate(self.query_history[-10:], 1):
                        cprint(f"  {h['time']} - {h['q'][:50]}...", Colors.BLUE)
                    print()
                    continue
                
                if user_input.startswith("ask "):
                    question = user_input[4:]
                    if self.current_patient:
                        patient_data = self.openemr_api.get_patient_data(self.current_patient)
                        self.query(question, patient_data)
                    else:
                        self.query(question)
                
                elif user_input.startswith("patient "):
                    patient_id = user_input.split()[1]
                    self.show_patient_summary(patient_id)
                
                elif user_input.startswith("analyze "):
                    patient_id = user_input.split()[1]
                    self.quick_clinical_queries(patient_id)
                
                else:
                    if self.current_patient:
                        patient_data = self.openemr_api.get_patient_data(self.current_patient)
                        self.query(user_input, patient_data)
                    else:
                        self.query(user_input)
                        
            except (EOFError, KeyboardInterrupt):
                self.openemr_api.stop_ssh_tunnel()
                break


def main():
    rag = OpenEMRRAG()
    
    if not rag.load_existing_vectorstore():
        rag.ingest_knowledge_base()
    
    rag.setup_qa_chain()
    rag.interactive_mode()


if __name__ == "__main__":
    main()
