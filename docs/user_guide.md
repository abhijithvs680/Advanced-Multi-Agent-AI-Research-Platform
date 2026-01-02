# User Guide - Multi-Agent AI Research Platform

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Creating Research Jobs](#creating-research-jobs)
4. [Monitoring Jobs](#monitoring-jobs)
5. [Understanding Results](#understanding-results)
6. [Exporting Reports](#exporting-reports)
7. [Advanced Features](#advanced-features)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### First-Time Setup

1. **Start the Platform**
   ```bash
   docker-compose up --build -d
   docker-compose exec app alembic upgrade head
   ```

2. **Configure LLM (Optional)**
   ```bash
   # Edit .env file
   OPENAI_API_KEY=sk-your-key
   ```

3. **Access Dashboard**
   Open http://localhost:3001 in your browser.

### System Requirements

- Modern web browser (Chrome, Firefox, Edge)
- Stable internet connection for paper search
- API keys for full LLM features

---

## Dashboard Overview

### Main Sections

| Section | Purpose |
|---------|---------|
| **Metrics Grid** | Queue length, running jobs, success rate |
| **Recent Jobs** | Quick access to latest research |
| **Quick Actions** | Create job, view all jobs |

### Navigation

- **Dashboard** - Overview and metrics
- **Jobs** - All research jobs
- **Create Job** - Start new research
- **Settings** - System status and configuration

### Status Indicators

- 🟢 **Completed** - Successful research
- 🔵 **Running** - Currently processing
- 🟡 **Pending** - Waiting in queue
- 🔴 **Failed** - Encountered error
- ⚪ **Cancelled** - Stopped by user

---

## Creating Research Jobs

### Step 1: Click "Create Job"

From the sidebar or dashboard, click the **Create Job** button.

### Step 2: Enter Research Topic

**Example topics:**
- "Transformer architectures for time series forecasting"
- "Federated learning for healthcare data"
- "Graph neural networks for drug discovery"

**Tips:**
- Be specific but not too narrow
- Include the problem type (classification, forecasting, etc.)
- Mention the domain context

### Step 3: Select Domain

Choose from suggestions or type custom:
- AI, Machine Learning, Deep Learning
- NLP, Computer Vision, Robotics
- Healthcare, Finance, Climate

### Step 4: Set Priority (Optional)

| Priority | Behavior |
|----------|----------|
| Normal | Standard queue processing |
| High | Processed before normal |
| Urgent | Processed first |

### Step 5: Submit

Click **Create Job** to submit. You'll be redirected to the job details page.

---

## Monitoring Jobs

### Job List View

**Filters:**
- Status: All, Pending, Running, Completed, Failed
- Domain: Filter by research domain

**Actions:**
- 👁️ View details
- ❌ Cancel (running/pending)
- 🔄 Retry (failed)
- 🗑️ Delete

### Job Details View

**Workflow Progress:**
```
Initialized → Research → Data Collection → Training → Evaluation → Completed
```

**Information Displayed:**
- Created/Started/Completed timestamps
- Duration
- Retry count
- MLflow experiment link

**Results Section:**
- Best model type and score
- All trained models comparison
- Statistical analysis

**Execution Timeline:**
- Step-by-step history
- Metrics at each stage

---

## Understanding Results

### Research Output

**Literature Analysis:**
- Summary of relevant papers
- Key findings and methodologies
- Research gaps identified
- Emerging trends

**Hypotheses:**
- 3-5 novel research hypotheses
- Novelty scores (0-1)
- Required experiments

### Model Results

The **Training** tab visualizes the model building process. It has two modes depending on the data available:

**1. Detailed Comparison View**
(Available when full metrics are computed)
- **Best Model**: Highlighted properly with its type (e.g., Random Forest) and primary score.
- **Model Comparison Chart**: A bar chart comparing accuracy across all trained models (RF, XGBoost, Neural Nets).
- **Hyperparameters**: detailed view of the configuration used for the best model.

**2. Summary View**
(Fallback for legacy or simple runs)
- Displays key metrics: Best Accuracy, Total Models Trained, and Training Time.
- Shows a notification if detailed comparisons are unavailable.

**Metrics Tracked:**
- **Accuracy**: Overall correctness.
- **F1 Score**: Balance between precision and recall (crucial for imbalanced data).
- **AUC-ROC**: Ability to distinguish between classes.
- **Training Time**: Efficiency of the model.

**Explanations:**
- **Feature Importance**: Which variables drove the decisions.
- **SHAP Values**: Detailed contribution of each feature (if enabled).

> **Note on Persistence**: The system automatically saves progress. You can refresh the page or close the browser tab without losing the current job state. When you return, the live data will reconnect automatically.

### Statistical Analysis

**Significance Tests:**
- p-values (< 0.05 = significant)
- Confidence intervals
- Effect size (Cohen's d)

**Ablation Study:**
- Component importance
- Impact of each feature

---

## Exporting Reports

### Available Formats

| Format | Best For |
|--------|----------|
| **PDF** | Sharing, printing |
| **LaTeX** | Academic papers |
| **Jupyter** | Interactive analysis |
| **Markdown** | Documentation |

### How to Export

1. Open job details
2. Click **Export** button
3. Select format
4. Download file

### Report Contents

- Executive summary
- Literature review
- Methodology
- Results and figures
- Statistical analysis
- References

---

## Advanced Features

### Real-Time Updates

Jobs update in real-time via WebSocket. You'll see:
- Live status changes
- Agent progress indicators
- Metrics as they're computed

### Knowledge Graph

The platform stores research artifacts:
- Papers and citations
- Experiments and results
- Models and metrics
- Hypotheses and lineage

### Multi-Model Comparison

The platform automatically trains multiple models:
- Random Forest
- Gradient Boosting
- Logistic Regression
- Neural Networks

All models are compared with proper statistical tests.

---

## Troubleshooting

### Common Issues

**UI not loading?**
```bash
docker-compose logs frontend
docker-compose restart frontend
```

**Jobs stuck in pending?**
```bash
docker-compose logs app
docker-compose restart app
```

**Database errors?**
```bash
docker-compose exec app alembic upgrade head
```

**Services offline?**
```bash
docker-compose ps
docker-compose up -d
```

### Checking Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f frontend
```

### Reset Everything

⚠️ **Warning: This deletes all data!**

```bash
docker-compose down -v
docker-compose up --build -d
docker-compose exec app alembic upgrade head
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `/` | Focus search |
| `n` | New job (from Jobs page) |
| `r` | Refresh current view |
| `Esc` | Close modals |

---

## Getting Help

- **API Docs**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Logs**: `docker-compose logs`

---

## Tips for Best Results

1. **Be Specific** - Detailed topics yield better research
2. **Check Papers** - Review literature findings
3. **Monitor Progress** - Watch real-time updates
4. **Export Results** - Save important findings
5. **Retry Failed Jobs** - Transient errors are common
