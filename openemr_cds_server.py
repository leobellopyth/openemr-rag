#!/usr/bin/env python3
"""
OpenEMR Clinical Decision Support Server
REST API for Lovable frontend integration
"""

import json
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import requests
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuration
OPENEMR_HOST = "16.58.52.89"
OPENEMR_API_PORT = 3001
SERVER_PORT = 3002

# Global state
ssh_tunnel_process = None
rag_system = None

# SSH Tunnel Management
def start_ssh_tunnel():
    global ssh_tunnel_process
    try:
        subprocess.run(['taskkill', '/F', '/IM', 'ssh.exe'], 
                     stderr=subprocess.DEVNULL, timeout=2)
    except:
        pass
    
    ssh_tunnel_process = subprocess.Popen(
        ['ssh', '-i', 'C:\\Users\\leobe\\.ssh\\OpenEMRLeo.pem',
         '-N', '-L', f'{OPENEMR_API_PORT}:localhost:{OPENEMR_API_PORT}',
         f'ubuntu@{OPENEMR_HOST}'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(2)
    return ssh_tunnel_process.poll() is None

def stop_ssh_tunnel():
    global ssh_tunnel_process
    if ssh_tunnel_process:
        ssh_tunnel_process.terminate()
        ssh_tunnel_process = None

# OpenEMR API Client
class OpenEMRClient:
    def __init__(self):
        self.base_url = f"http://localhost:{OPENEMR_API_PORT}"
    
    def get_patient(self, patient_id):
        try:
            resp = requests.get(f"{self.base_url}/api/patient/{patient_id}", timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return None
    
    def get_patient_summary(self, patient_id):
        data = self.get_patient(patient_id)
        if not data:
            return None
        
        name = data.get('name', {})
        dob = data.get('birthDate', '')
        if dob:
            dob = str(dob)[:10]
        
        return {
            "id": data.get("id"),
            "name": f"{name.get('given', '')} {name.get('family', '')}".strip(),
            "birthDate": dob,
            "gender": data.get("gender", "unknown"),
            "conditions": data.get("conditions", []),
            "medications": data.get("medications", []),
            "allergies": data.get("allergies", []),
            "vitals": data.get("vitals", [])[:5],
            "socialHistory": data.get("socialHistory", [])
        }

# RAG System
def init_rag():
    global rag_system
    if rag_system is None:
        from openemr_rag import OpenEMRRAG
        rag_system = OpenEMRRAG()
        rag_system.load_existing_vectorstore()
        rag_system.setup_qa_chain()
    return rag_system

# Demo patients for demo mode
DEMO_PATIENTS = {
    "1": {
        "id": "1",
        "name": "Sarah Johnson",
        "birthDate": "1978-05-15",
        "gender": "female",
        "conditions": [
            {"title": "Type 2 Diabetes", "diagnosis": "ICD10:E11.9"},
            {"title": "Hypertension", "diagnosis": "ICD10:I10"}
        ],
        "medications": [
            {"drug": "Metformin 500mg", "dosage": "twice daily", "active": 1},
            {"drug": "Lisinopril 10mg", "dosage": "once daily", "active": 1}
        ],
        "allergies": [{"title": "Penicillin", "reaction": "Hives"}],
        "vitals": [
            {"date": "2026-03-15", "bps": "138", "bpd": "88", "pulse": "78", "oxygen_saturation": "97"}
        ],
        "socialHistory": []
    },
    "2": {
        "id": "2",
        "name": "Michael Chen",
        "birthDate": "1965-11-22",
        "gender": "male",
        "conditions": [
            {"title": "COPD", "diagnosis": "ICD10:J44.9"},
            {"title": "CHF", "diagnosis": "ICD10:I50.9"}
        ],
        "medications": [
            {"drug": "Albuterol inhaler", "dosage": "as needed", "active": 1},
            {"drug": "Furosemide 40mg", "dosage": "once daily", "active": 1}
        ],
        "allergies": [],
        "vitals": [
            {"date": "2026-03-18", "bps": "142", "bpd": "90", "pulse": "92", "oxygen_saturation": "94"}
        ],
        "socialHistory": [{"title": "Former smoker"}]
    },
    "3": {
        "id": "3",
        "name": "Emily Rodriguez",
        "birthDate": "1990-03-08",
        "gender": "female",
        "conditions": [
            {"title": "Asthma", "diagnosis": "ICD10:J45.909"}
        ],
        "medications": [
            {"drug": "Fluticasone inhaler", "dosage": "twice daily", "active": 1}
        ],
        "allergies": [{"title": "Sulfa drugs", "reaction": "Anaphylaxis"}],
        "vitals": [
            {"date": "2026-03-19", "bps": "118", "bpd": "76", "pulse": "72", "oxygen_saturation": "99"}
        ],
        "socialHistory": []
    }
}

# Routes
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "mode": "live" if ssh_tunnel_process else "demo"})

@app.route('/connect', methods=['POST'])
def connect():
    if start_ssh_tunnel():
        return jsonify({"status": "connected", "mode": "live"})
    return jsonify({"status": "failed", "mode": "demo"})

@app.route('/disconnect', methods=['POST'])
def disconnect():
    stop_ssh_tunnel()
    return jsonify({"status": "disconnected"})

@app.route('/patient/<patient_id>', methods=['GET'])
def get_patient(patient_id):
    mode = request.args.get('mode', 'live')
    
    if mode == 'demo':
        patient = DEMO_PATIENTS.get(patient_id)
        if patient:
            return jsonify(patient)
        return jsonify({"error": "Demo patient not found"}), 404
    
    # Live mode
    client = OpenEMRClient()
    patient = client.get_patient_summary(patient_id)
    
    if patient:
        return jsonify(patient)
    return jsonify({"error": "Patient not found"}), 404

@app.route('/patients', methods=['GET'])
def list_patients():
    mode = request.args.get('mode', 'demo')
    
    if mode == 'demo':
        return jsonify(list(DEMO_PATIENTS.values()))
    
    # For live mode, return basic list (would need pagination in production)
    return jsonify([])

@app.route('/query', methods=['POST'])
def clinical_query():
    data = request.get_json()
    question = data.get('question', '')
    patient_id = data.get('patient_id')
    mode = data.get('mode', 'demo')
    
    if not question:
        return jsonify({"error": "Question required"}), 400
    
    # Get patient context if provided
    patient_context = None
    if patient_id:
        if mode == 'demo':
            patient_context = DEMO_PATIENTS.get(patient_id)
        else:
            client = OpenEMRClient()
            patient_context = client.get_patient(patient_id)
    
    # Use RAG system
    try:
        rag = init_rag()
        result = rag.query(question, patient_context)
        return jsonify({"answer": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze/<analysis_type>', methods=['POST'])
def analyze(analysis_type):
    data = request.get_json()
    patient_id = data.get('patient_id')
    mode = data.get('mode', 'demo')
    
    if not patient_id:
        return jsonify({"error": "Patient ID required"}), 400
    
    # Get patient data
    if mode == 'demo':
        patient = DEMO_PATIENTS.get(patient_id)
    else:
        client = OpenEMRClient()
        patient = client.get_patient(patient_id)
    
    if not patient:
        return jsonify({"error": "Patient not found"}), 404
    
    # Analysis prompts
    prompts = {
        "vitals": "Analyze these vital signs. Identify any concerning values or trends. Provide clinical recommendations.\n\nPatient Data:\n",
        "medications": "Review these medications. Check for interactions, appropriateness, and potential optimizations.\n\nPatient Data:\n",
        "risks": "Based on this patient's conditions, medications, and history, what are the top 3 clinical risks or concerns?\n\nPatient Data:\n",
        "gaps": "What preventive care or chronic disease management gaps exist for this patient?\n\nPatient Data:\n"
    }
    
    question = prompts.get(analysis_type, "Provide clinical insights for this patient.\n\nPatient Data:\n")
    
    try:
        rag = init_rag()
        result = rag.query(question, patient)
        return jsonify({
            "type": analysis_type,
            "patient_id": patient_id,
            "analysis": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("=" * 60)
    print("  OpenEMR Clinical Decision Support Server")
    print(f"  API Running on http://localhost:{SERVER_PORT}")
    print("=" * 60)
    print()
    print("Endpoints:")
    print("  GET  /health           - Health check")
    print("  POST /connect          - Connect to OpenEMR")
    print("  POST /disconnect       - Disconnect from OpenEMR")
    print("  GET  /patient/<id>     - Get patient data")
    print("  GET  /patients         - List patients (demo)")
    print("  POST /query            - Clinical query")
    print("  POST /analyze/<type>   - Analysis (vitals|meds|risks|gaps)")
    print()
    
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=False)
