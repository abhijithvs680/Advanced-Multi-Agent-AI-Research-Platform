# 🧠 Multi-Agent AI Research Platform: Explanation

## 🎯 What this application does

The **Multi-Agent AI Research Platform** is an autonomous "AI Principal Investigator" designed to conduct end-to-end scientific research with minimal human intervention. It coordinates a team of specialized AI agents to handle the entire research lifecycle:

1.  **Literature Review**: Searches academic databases like Semantic Scholar and arXiv to find relevant papers.
2.  **Hypothesis Generation**: Uses Large Language Models (LLMs) to synthesize information and propose novel research ideas.
3.  **Data Collection**: Gathers data from multiple sources and provides quality reports.
4.  **Model Training**: Automatically trains machine learning models, optimizes hyperparameters using Optuna, and tracks experiments with MLflow.
5.  **Evaluation**: Performs statistical tests and generates publication-ready research reports in various formats (PDF, LaTeX, Jupyter).

---

## 🚀 How to use this application

### 1. Setup and Installation
The application is containerized for easy deployment.
*   **Prerequisites**: Docker, Docker Compose, and Node.js.
*   **Configuration**: Set your `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in the `.env` file.
*   **Startup**: Run `docker-compose up --build -d` to launch all services.

### 2. Interfacing with the Platform
You can interact with the system in three ways:
*   **Dashboard**: A React-based UI available at `http://localhost:3001` for monitoring research progress in real-time.
*   **API**: A FastAPI server at `http://localhost:8000`. You can start research jobs by sending a POST request to `/api/v1/jobs` with a topic and domain.
*   **Monitoring Tools**:
    *   **MLflow** (`http://localhost:5000`): View model training metrics and artifacts.
    *   **Grafana** (`http://localhost:3000`): Monitor system health and performance.

### 3. Workflow Example
To start a new research project:
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Transformer architectures for climate prediction",
    "domain": "Climate Science",
    "priority": 1
  }'
```
Once submitted, the **Orchestration Layer** will assign tasks to the **Research**, **Data**, **Training**, and **Evaluation** agents sequentially.

---

## 💡 For what purpose was it created?

The platform was built to address the bottleneck in scientific research by automating the most time-consuming parts of the process:

*   **Scalability**: Conduct multiple research projects simultaneously.
*   **Reproducibility**: Maintain a strict lineage of data and experiments via a Knowledge Graph and MLflow.
*   **Efficiency**: Rapidly iterate from a research question to a trained model and a finalized report.
*   **Accessibility**: Provide a unified interface for researchers to leverage advanced LLM capabilities and specialized tools without deep knowledge of the underlying infrastructure.

---

## 🏗️ Technical Architecture

*   **Frontend**: React with TypeScript and Vite.
*   **Backend**: FastAPI (Python) with a WebSocket layer for real-time updates.
*   **Agents**: Python-based autonomous agents using a message-passing architecture.
*   **Task Queue**: Redis for asynchronous job processing.
*   **Database**: PostgreSQL for persistent storage and DuckDB for case-specific data.
*   **Experiment Tracking**: MLflow.
*   **Orchestration**: Custom decision and discovery engines to manage agent workflows.
