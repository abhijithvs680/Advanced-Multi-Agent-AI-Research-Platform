# API Reference

## Base URLs

- **Core API**: `http://localhost:8000/api/v1`
- **Health & Metrics**: `http://localhost:8000/`

## Authentication

Currently open access. Enterprise version supports JWT authentication.

---

## Jobs Endpoints

All job endpoints are prefixed with `/api/v1`.

### Create Job

```http
POST /jobs
```

**Request Body:**

```json
{
  "topic": "string (required)",
  "domain": "string (default: 'general')",
  "priority": "integer (1-10, default: 5)"
}
```

**Response:**

```json
{
  "id": "uuid",
  "topic": "string",
  "domain": "string",
  "status": "pending",
  "created_at": "datetime",
  "priority": 5
}
```

---

### List Jobs

```http
GET /jobs
```

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| status | string | Filter by status |
| domain | string | Filter by domain |
| page | int | Page number (default: 1) |
| limit | int | Items per page (default: 20) |

**Response:**

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "pages": 5
}
```

---

### Get Job

```http
GET /jobs/{job_id}
```

**Response:**

```json
{
  "id": "uuid",
  "topic": "string",
  "domain": "string",
  "status": "completed",
  "result": {...},
  "execution_history": [...],
  "created_at": "datetime",
  "started_at": "datetime",
  "completed_at": "datetime",
  "mlflow_run_id": "string"
}
```

---

### Cancel Job

```http
POST /jobs/{job_id}/cancel
```

**Response:**

```json
{
  "success": true,
  "message": "Job cancelled"
}
```

---

### Retry Job

```http
POST /jobs/{job_id}/retry
```

**Response:**

```json
{
  "id": "uuid",
  "status": "pending"
}
```

---

### Delete Job

```http
DELETE /jobs/{job_id}
```

**Response:**

```json
{
  "success": true
}
```

---

### Export Job Report

```http
GET /jobs/{job_id}/export
```

**Query Parameters:**

| Param | Type | Options |
|-------|------|---------|
| format | string | pdf, latex, jupyter, markdown |

**Response:** File download

---

## Health & Metrics Endpoints

These endpoints are available at the root level (no `/api/v1` prefix).

### Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "datetime"
}
```

---

### Readiness

```http
GET /ready
```

**Response:**

```json
{
  "status": "ready",
  "services": {
    "database": true,
    "redis": true,
    "mlflow": true
  }
}
```

---

### Metrics

```http
GET /metrics
```

**Response:** Prometheus format metrics

---

## WebSocket Endpoints

### Main WebSocket

```
ws://localhost:8000/ws
```

**Client Messages:**

```json
{
  "action": "subscribe",
  "job_id": "uuid"
}
```

**Server Events:**

```json
{
  "type": "job_status",
  "job_id": "uuid",
  "data": {
    "status": "running",
    "progress": 0.5
  },
  "timestamp": "datetime"
}
```

---

### Job-Specific WebSocket

```
ws://localhost:8000/ws/job/{job_id}
```

Auto-subscribes to job updates.

---

## Error Responses

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE"
}
```

**Common Error Codes:**

| Code | Status | Description |
|------|--------|-------------|
| NOT_FOUND | 404 | Job not found |
| VALIDATION_ERROR | 422 | Invalid input |
| INTERNAL_ERROR | 500 | Server error |
| CONFLICT | 409 | Invalid state transition |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Create Job | 10/min |
| List Jobs | 100/min |
| WebSocket | 5 connections |

---

## SDK Usage

### Python

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000/api/v1")

# Create job
response = client.post("/jobs", json={
    "topic": "Deep learning for NLP",
    "domain": "AI"
})
job = response.json()

# Get status
status = client.get(f"/jobs/{job['id']}").json()
```

### JavaScript

```javascript
const response = await fetch('http://localhost:8000/api/v1/jobs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    topic: 'Deep learning for NLP',
    domain: 'AI'
  })
});
const job = await response.json();
```

---

## OpenAPI Spec

Full OpenAPI specification available at:

```
http://localhost:8000/openapi.json
```

Interactive docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
