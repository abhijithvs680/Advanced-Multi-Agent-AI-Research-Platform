# 🧠 Multi-Agent AI Research Platform

<div align="center">

**Autonomous AI Research System with Multi-Agent Orchestration**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[Quick Start](#-quick-start) • [Features](#-features) • [Documentation](#-documentation) • [API](#-api-reference) • [Contributing](#-contributing)

</div>

---

## 🎯 Overview

A production-grade **AI Principal Investigator** that autonomously conducts end-to-end scientific research:

- 🔍 **Literature Review** - Searches Semantic Scholar & arXiv
- 💡 **Hypothesis Generation** - LLM-powered novel idea creation
- 📊 **Data Collection** - Multi-source with quality reports
- 🎓 **Model Training** - Optuna optimization + SHAP explanations
- 📈 **Evaluation** - Statistical tests + publication-ready reports

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.10+ (for local development)

### 1. Clone & Setup

```bash
git clone https://github.com/your-org/multi-agent-research-platform.git
cd multi-agent-research-platform
cp .env.example .env
```

### 2. Configure API Keys (Optional)

```bash
# Edit .env file with your API keys
OPENAI_API_KEY=sk-xxx          # For LLM features
ANTHROPIC_API_KEY=sk-ant-xxx    # Alternative LLM
```

### 3. Launch Services

```bash
docker-compose up --build -d
```

### 4. Initialize Database

```bash
docker-compose exec app alembic upgrade head
```

### 5. Access the Platform

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | http://localhost:3001 | React UI |
| **API Docs** | http://localhost:8000/docs | Swagger |
| **MLflow** | http://localhost:5000 | Experiments |
| **Grafana** | http://localhost:3000 | Metrics |

---

## ✨ Features

### 🤖 Intelligent Agents

| Agent | Capabilities |
|-------|-------------|
| **Research** | Literature search, hypothesis generation, methodology design |
| **Data** | Multi-source collection, feature engineering, quality reports |
| **Training** | Hyperparameter optimization, model explanations, MLflow tracking |
| **Evaluation** | Statistical tests, ablation studies, publication figures |

### 🧠 AI Capabilities

- **LLM Integration** - OpenAI GPT-4 & Anthropic Claude
- **Paper Search** - Semantic Scholar & arXiv APIs
- **Knowledge Graph** - Persistent artifact storage with lineage
- **Real-time Updates** - WebSocket live progress

### 📦 Export Formats

- 📄 PDF Reports
- 📝 LaTeX Documents
- 📓 Jupyter Notebooks
- 📋 Markdown Summaries

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Dashboard                      │
│               (Real-time WebSocket Updates)             │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    FastAPI Server                       │
│        /jobs  /health  /metrics  /ws  /export           │
└─────┬───────────────┬───────────────┬───────────────────┘
      │               │               │
┌─────▼─────┐  ┌──────▼──────┐  ┌─────▼─────┐
│  Redis    │  │  PostgreSQL │  │  MLflow   │
│  Queue    │  │  Database   │  │  Tracking │
└─────┬─────┘  └─────────────┘  └───────────┘
      │
┌─────▼─────────────────────────────────────────────────┐
│                   Worker Pool                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Research │ │   Data   │ │ Training │ │  Eval    │  │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└───────────────────────────────────────────────────────┘
```

---

## 📖 API Reference

### Create Research Job

```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Transformer architectures for time series",
    "domain": "Machine Learning",
    "priority": 1
  }'
```

### Get Job Status

```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}"
```

### List All Jobs

```bash
curl "http://localhost:8000/api/v1/jobs?status=completed&page=1"
```

### Cancel Job

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/{job_id}/cancel"
```

### Export Report

```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}/export?format=pdf"
```

See full API documentation at http://localhost:8000/docs

---

## 🔧 Development

### Backend Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start dependencies
docker-compose up postgres redis mlflow -d

# Run API server
python scripts/run_service.py
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Coverage report
pytest --cov=agents --cov=api --cov-report=html
```

---

## 📁 Project Structure

```
├── agents/                 # AI agent implementations
│   ├── research_agent/     # Literature review & hypothesis
│   ├── data_agent/         # Data collection & processing
│   ├── training_agent/     # Model training & optimization
│   └── evaluation_agent/   # Evaluation & reporting
│
├── api/                    # FastAPI server
│   ├── routes/             # API endpoints
│   ├── schemas.py          # Pydantic models
│   └── server.py           # App configuration
│
├── frontend/               # React TypeScript UI
│   ├── src/
│   │   ├── components/     # Reusable components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom hooks
│   │   └── api/            # API client
│   └── package.json
│
├── shared/                 # Common utilities
│   ├── llm_client.py       # LLM integration
│   ├── paper_search.py     # Academic APIs
│   ├── knowledge_graph.py  # Artifact storage
│   └── export.py           # Report generation
│
├── orchestration/          # Workflow engine
├── workers/                # Job processors
├── tests/                  # Test suites
├── docs/                   # Documentation
└── docker-compose.yml      # Service definitions
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://...` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `MLFLOW_TRACKING_URI` | MLflow server | `http://localhost:5000` |
| `NUM_WORKERS` | Concurrent workers | `2` |

---

## 📊 Monitoring

- **Health Check**: `GET /health`
- **Readiness**: `GET /ready`
- **Metrics**: `GET /metrics`
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [MLflow](https://mlflow.org/) - Experiment tracking
- [Semantic Scholar](https://www.semanticscholar.org/) - Paper API
- [Optuna](https://optuna.org/) - Hyperparameter optimization
- [SHAP](https://shap.readthedocs.io/) - Model explanations
