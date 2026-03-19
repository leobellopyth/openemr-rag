# Contributing to OpenEMR Clinical Decision Support System

Thank you for your interest in contributing!

## How to Contribute

### Reporting Issues
- Use GitHub Issues for bug reports
- Include system specifications (OS, Python version, Ollama version)
- Provide sample queries that reproduce the issue

### Suggesting Features
- Open a GitHub Discussion first
- Describe the use case and expected behavior
- Consider privacy and security implications

### Pull Requests
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes with clear messages
4. Push to your fork
5. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/openemr-rag.git
cd openemr-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install in development mode
pip install -r requirements.txt

# Run tests
python -c "from openemr_rag import OpenEMRRAG"
```

## Code Style
- Follow PEP 8
- Use type hints where helpful
- Document complex functions

## Security
- Never commit credentials or API keys
- Keep patient data local
- Report security issues privately
