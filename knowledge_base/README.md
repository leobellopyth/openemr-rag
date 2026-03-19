# OpenEMR RAG System - Knowledge Base

This folder contains documents that will be indexed for the RAG system.

## Folder Structure

```
knowledge_base/
├── openemr_docs/         # OpenEMR documentation, FHIR specs, API docs
├── clinical_guidelines/   # Clinical practice guidelines, protocols
├── drug_database/        # Drug interaction information
└── institutional/       # Custom institutional protocols
```

## Adding Documents

1. **OpenEMR Documentation**
   - Download from: https://www.openemr.org/wiki/index.php/OpenEMR_Downloads
   - Place .txt files in `openemr_docs/`

2. **Clinical Guidelines**
   - Add relevant CPGs as .txt files in `clinical_guidelines/`

3. **Drug Database**
   - FDA drug labels, interaction databases
   - Place in `drug_database/`

## Supported Formats

- `.txt` - Plain text (primary)
- `.md` - Markdown (converted to text)
- PDF support via pypdf (install separately)

## Initial Setup

The first time you run the system, it will:
1. Connect to Ollama at localhost:11434
2. Use medgemma:4b model for medical context
3. Index all documents in this folder
4. Create a persistent vector store in `../vector_store/`

## Tips

- Use clear, well-formatted documents for better results
- Include source citations in documents
- Break long documents into logical sections
