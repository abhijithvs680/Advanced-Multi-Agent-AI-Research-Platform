# Multi-Agent Research Platform - Quick Start

## Overview

The system has been converted from batch-style execution to a **long-running service platform** with:
- ✅ RESTful API for job management
- ✅ Redis job queue with priority support
- ✅ PostgreSQL for persistent state
- ✅ Concurrent workflow workers
- ✅ Prometheus metrics + Grafana dashboards
- ✅ Health checks and graceful shutdown

## Quick Start

### 1. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit API keys (optional for testing)
# nano .env
```

### 2. Launch Services
```bash
# Stop old containers
docker-compose down -v

# Build and start
docker-compose up --build -d

# Check status
docker-compose ps
```

### 3. Run Migrations
```bash
docker-compose exec app alembic upgrade head
```

### 4. Access Services
- **API Docs**: http://localhost:8000/docs
- **MLflow**: http://localhost:5000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

## Usage

### Create a Job
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{"topic": "machine learning", "domain": "AI"}'
```

### Check Job Status
```bash
curl "http://localhost:8000/api/v1/jobs/{job_id}"
```

### List Jobs
```bash
curl "http://localhost:8000/api/v1/jobs"
```

### Cancel Job
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/{job_id}/cancel"
```

### Monitor Metrics
```bash
curl "http://localhost:8000/metrics"
```

## Architecture

```
External → FastAPI → PostgreSQL (Jobs)
              ↓
           Redis Queue
              ↓
         Worker Pool → MLflow
              ↓
         Prometheus → Grafana
```

## Key Files

- `scripts/run_service.py` - Main entry point
- `api/server.py` - FastAPI application
- `api/routes/jobs.py` - Job management endpoints
- `workers/workflow_worker.py` - Job processor
- `shared/queue.py` - Redis job queue
- `shared/models.py` - Database models

## Environment Variables

See `.env.example` for all configuration options.

Key variables:
- `NUM_WORKERS` - Number of concurrent workers (default: 2)
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

### Readiness
```bash
curl http://localhost:8000/ready
```

### Prometheus Metrics
```bash
curl http://localhost:8000/metrics/prometheus
```

## Troubleshooting

### View Logs
```bash
docker-compose logs -f app
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
docker-compose exec app alembic upgrade head
```

### Queue Issues
```bash
# Check Redis
docker-compose exec redis redis-cli ping
docker-compose exec redis redis-cli KEYS '*'
```

## Success Criteria ✅

- Container runs indefinitely
- Jobs processed via API
- Concurrent execution
- Persistent state
- Metrics exposed
- Graceful shutdown

For detailed documentation, see `walkthrough.md`.
