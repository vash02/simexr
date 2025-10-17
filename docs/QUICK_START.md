# Quick Start Guide

Get up and running with SimExR in minutes!

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Git
- OpenAI API key

### Setup Steps

```bash
# 1. Clone repository
git clone <repository-url>
cd simexr_mod

# 2. Create virtual environment
python -m venv simexr_venv
source simexr_venv/bin/activate  # Windows: simexr_venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cp config.yaml.example config.yaml
# Edit config.yaml and add your OpenAI API key

# 5. Start the system
python start_streamlit.py  # Starts both API and web UI
```

## 🎯 First Steps

### Option 1: Web Interface
1. Open http://localhost:8501
2. Go to "Import Models" page
3. Enter a GitHub URL
4. Run simulations and ask AI questions

### Option 2: API Direct
```bash
# Import model
curl -X POST "http://localhost:8000/simulation/transform/github" \
  -d '{"github_url": "https://github.com/vash02/physics-systems-dataset/blob/main/vanderpol.py", "model_name": "test_model"}'

# Run simulation
curl -X POST "http://localhost:8000/simulation/run" \
  -d '{"model_id": "your_model_id", "parameters": {"mu": 1.5}}'
```

## ✅ Verification

Check that everything works:
- API: http://localhost:8000/docs
- Web UI: http://localhost:8501
- Health: http://localhost:8000/health/status

[← Back to Documentation](index.md)
