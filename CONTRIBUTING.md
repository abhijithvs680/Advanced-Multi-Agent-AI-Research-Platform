# Contributing to Multi-Agent Research Platform

Thank you for your interest in contributing! 🎉

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

---

## Code of Conduct

Be respectful, inclusive, and constructive. We're all here to learn and build together.

---

## Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR-USERNAME/multi-agent-research-platform.git
   cd multi-agent-research-platform
   ```
3. **Add upstream**:
   ```bash
   git remote add upstream https://github.com/original/multi-agent-research-platform.git
   ```

---

## Development Setup

### Backend

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Start services
docker-compose up postgres redis mlflow -d

# Run server
python scripts/run_service.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

---

## Making Changes

### Branch Naming

```
feature/add-new-agent
fix/job-cancellation-bug
docs/update-readme
refactor/improve-queue
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add multi-modal data support
fix: resolve WebSocket connection timeout
docs: update API reference
test: add unit tests for training agent
refactor: simplify workflow orchestration
```

---

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Single file
pytest tests/unit/test_agents.py -v
```

### Coverage Report

```bash
pytest --cov=agents --cov=api --cov-report=html
open htmlcov/index.html
```

### Minimum Coverage

- New code: 80%
- Critical paths: 90%

---

## Pull Request Process

1. **Update your fork**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make changes and commit**

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature
   ```

5. **Open Pull Request**:
   - Fill out the PR template
   - Link related issues
   - Add reviewers

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Commits are clean and meaningful

---

## Style Guidelines

### Python

Follow [PEP 8](https://peps.python.org/pep-0008/) with these additions:

```python
# Imports ordered: stdlib, third-party, local
import os
import asyncio

import pandas as pd
from fastapi import FastAPI

from shared.logger import get_logger


# Type hints required
async def process_job(job_id: str) -> Dict[str, Any]:
    """Process a research job.
    
    Args:
        job_id: Unique job identifier
        
    Returns:
        Job result dictionary
    """
    pass


# Docstrings for public functions
# Use Google style docstrings
```

### TypeScript/React

```typescript
// Functional components with TypeScript
interface JobCardProps {
  job: Job;
  onSelect: (id: string) => void;
}

const JobCard: React.FC<JobCardProps> = ({ job, onSelect }) => {
  // Component logic
  return <div>...</div>;
};

// Use hooks, not class components
// Prefer named exports
```

### Formatting

- Python: `black`, `isort`, `flake8`
- TypeScript: `prettier`, `eslint`

Run formatters:
```bash
# Python
black .
isort .

# TypeScript
npm run format
npm run lint
```

---

## Project Structure

```
├── agents/           # Add new agents here
├── api/              # API endpoints
├── frontend/         # React UI
├── shared/           # Shared utilities
├── tests/            # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/             # Documentation
```

---

## Adding New Agents

1. Create directory: `agents/new_agent/`
2. Implement `agent.py` extending `BaseAgent`
3. Add to workflow orchestration
4. Write tests in `tests/unit/test_new_agent.py`
5. Document in `docs/agents/`

---

## Need Help?

- Open an issue for questions
- Join discussions
- Check existing issues first

---

Thank you for contributing! 🙏
