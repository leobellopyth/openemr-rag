# OpenEMR Clinical Decision Support System

A local RAG (Retrieval-Augmented Generation) system that enhances OpenEMR EMR with AI-powered clinical decision support capabilities.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Healthcare](https://img.shields.io/badge/Healthcare-Health%20Informatics-orange.svg)

## Overview

This project demonstrates a proof-of-concept for integrating local Large Language Models (LLMs) with OpenEMR to provide:
- Real-time clinical decision support
- Patient data analysis with context-aware AI responses
- Integration with AWS-hosted OpenEMR instances
- Privacy-preserving local AI processing

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LOCAL MACHINE                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  OpenEMR Clinical Decision Support System               │   │
│  │                                                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │   │
│  │  │   Ollama     │  │    FAISS     │  │  Knowledge   │ │   │
│  │  │  (medgemma)  │  │  Vector DB   │  │    Base      │ │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘ │   │
│  │         ▲                ▲                             │   │
│  │         └────────────────┴─────────────────────────────┘   │
│  │                    LangChain RAG Pipeline                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              │ SSH Tunnel                       │
└──────────────────────────────│──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         AWS EC2                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  OpenEMR 7.0.4 (Docker)                                │   │
│  │  ├── Apache/PHP Frontend                               │   │
│  │  ├── MySQL Database                                    │   │
│  │  └── ChartPrep Backend (Node.js) - REST API             │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Local LLM Processing**: Uses Ollama with medical-focused models (medgemma) for privacy
- **Clinical Knowledge Base**: RAG-powered retrieval from clinical guidelines
- **Patient Context**: Retrieves and analyzes real patient data from OpenEMR
- **Interactive CLI**: Color-coded terminal interface for clinical queries
- **Automated Analysis**: Pre-built clinical query templates

## Prerequisites

- **Hardware**: 16GB+ RAM recommended (tested on 63GB AMD Ryzen AI 9)
- **Software**:
  - Python 3.10+
  - [Ollama](https://ollama.ai/) installed and running
  - SSH client for tunnel to OpenEMR instance

### Ollama Setup

```bash
# Pull required models
ollama pull alibayram/medgemma:4b
ollama pull nomic-embed-text

# Verify models
ollama list
```

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/leobellopyth/openemr-rag.git
cd openemr-rag
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure OpenEMR connection**
- Edit `openemr_rag.py` with your OpenEMR host IP
- SSH credentials stored in `~/.ssh/OpenEMRLeo.pem`

4. **Run the system**
```bash
# Windows
Run-RAG-Interactive.bat

# Or directly
python openemr_rag.py
```

## Usage

### Interactive Commands

```
Commands:
  ask <question>     - Query with clinical guidelines
  patient <id>       - Load patient and show summary
  analyze <id>       - Run automated clinical analysis
  ?, help            - Show help
  history            - Show query history
  quit               - Exit
```

### Example Session

```
> patient 1
==================================================
  Patient Summary - #1
==================================================
  Name: Lyndon Blacksmith
  DOB: 1978-09-27
  Gender: male

  Conditions: 2
  Medications: 1
  Allergies: 0

  Latest Vitals:
    BP: 165/99 mmHg
    HR: 110 bpm
    SpO2: 90.00%

> Should I be concerned about these vitals?
Yes, you should be concerned about these vital signs:

* **Hypertension:** The patient's blood pressure (165/99 mmHg) is elevated
* **Tachycardia:** Heart rate (110 bpm) is elevated
* **Hypoxia:** Oxygen saturation (90%) is low and requires evaluation
```

## Project Structure

```
openemr-rag/
├── openemr_rag.py           # Main RAG application
├── requirements.txt         # Python dependencies
├── Run-RAG-Interactive.bat  # Windows launcher
├── knowledge_base/          # Clinical documents
│   └── clinical_guidelines/
├── vector_store/           # FAISS index (gitignored)
└── app/                    # Streamlit UI (future)
```

## Knowledge Base

The system includes clinical guidelines in `/knowledge_base/`:
- Sample clinical guidelines
- Reference values for vitals
- Red flag indicators

Add your own documents by creating `.txt` files in subdirectories.

## Security Considerations

- **Local Processing**: All LLM inference happens locally - patient data never leaves your machine
- **SSH Tunnel**: Encrypted connection to OpenEMR instance
- **No PHI Storage**: The RAG system doesn't persist PHI
- **Audit Trail**: Query history is stored in memory only

## Future Enhancements

- [ ] Streamlit web interface
- [ ] FHIR API integration
- [ ] Drug interaction checking
- [ ] Multi-modal support (imaging)
- [ ] SOAP note generation
- [ ] Discharge summary assistance

## License

MIT License - See LICENSE file for details.

## Author

**Leo Chow Bello**  
BScN, RN - Health Informatics Student  
George Brown College (Graduating April 2026)

## Acknowledgments

- OpenEMR community for the excellent EMR platform
- Ollama team for local LLM infrastructure
- Google for medgemma medical AI model

---

*This project is for educational and portfolio purposes. Not for production clinical use.*
