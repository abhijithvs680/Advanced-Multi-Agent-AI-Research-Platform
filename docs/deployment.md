# Deployment Guide

## Deployment Options

1. **Docker Compose** - Development & small-scale
2. **Kubernetes** - Production & enterprise
3. **Cloud Managed** - AWS/GCP/Azure

---

## Docker Compose Deployment

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 20GB disk space

### Quick Deploy

```bash
# Clone repository
git clone https://github.com/your-org/multi-agent-research-platform.git
cd multi-agent-research-platform

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start services
docker-compose up -d

# Initialize database
docker-compose exec app alembic upgrade head

# Check status
docker-compose ps
```

### Services Started

| Service | Port | Description |
|---------|------|-------------|
| app | 8000 | FastAPI server |
| frontend | 3001 | React UI |
| postgres | 5432 | Database |
| redis | 6379 | Job queue |
| mlflow | 5000 | Experiment tracking |
| prometheus | 9090 | Metrics |
| grafana | 3000 | Dashboards |

---

## Kubernetes Deployment

### Prerequisites

- Kubernetes 1.25+
- kubectl configured
- Helm 3.0+

### Deploy with Helm

```bash
# Add Helm repo (future)
helm repo add research-platform https://charts.example.com

# Install
helm install research-platform research-platform/multi-agent \
  --namespace research \
  --create-namespace \
  --set postgres.enabled=true \
  --set redis.enabled=true
```

### Manual Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace research-platform

# Apply configs
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/app.yaml
kubectl apply -f k8s/frontend.yaml

# Check status
kubectl get pods -n research-platform
```

### Sample Deployment Manifest

```yaml
# k8s/app.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-platform-api
  namespace: research-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: research-platform-api
  template:
    metadata:
      labels:
        app: research-platform-api
    spec:
      containers:
      - name: api
        image: research-platform:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: research-secrets
              key: database-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

---

## Cloud Deployments

### AWS

**Services Used:**
- ECS/EKS for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- S3 for MLflow artifacts

### GCP

**Services Used:**
- Cloud Run/GKE
- Cloud SQL
- Memorystore
- GCS for artifacts

### Azure

**Services Used:**
- AKS/Container Apps
- Azure Database for PostgreSQL
- Azure Cache for Redis
- Blob Storage

---

## Configuration

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/research
REDIS_URL=redis://localhost:6379

# Optional - LLM
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# Optional - Monitoring
MLFLOW_TRACKING_URI=http://mlflow:5000
PROMETHEUS_PORT=9090

# Optional - Scaling
NUM_WORKERS=4
MAX_CONCURRENT_JOBS=10
```

---

## Scaling

### Horizontal Scaling

```yaml
# HPA for API
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: research-platform-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Worker Scaling

Increase `NUM_WORKERS` environment variable for more concurrent job processing.

---

## Monitoring

### Prometheus Targets

- `app:8000/metrics` - API metrics
- `redis:9121/metrics` - Redis exporter
- `postgres:9187/metrics` - Postgres exporter

### Grafana Dashboards

Import dashboards from `monitoring/grafana/`:
- API Performance
- Job Queue Status
- Agent Metrics

---

## Backup & Recovery

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U postgres research > backup.sql

# Restore
docker-compose exec -T postgres psql -U postgres research < backup.sql
```

### MLflow Artifacts

Store on S3/GCS for durability:

```bash
MLFLOW_ARTIFACT_ROOT=s3://bucket/mlflow
```

---

## Security

### Production Checklist

- [ ] Change default passwords
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Set up authentication
- [ ] Enable audit logging
- [ ] Encrypt secrets
- [ ] Regular security updates

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: research-platform-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 8000
```

---

## Troubleshooting

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod <pod-name> -n research-platform
kubectl logs <pod-name> -n research-platform
```

**Database connection errors:**
- Check DATABASE_URL format
- Verify network connectivity
- Check credentials

**High memory usage:**
- Increase resource limits
- Scale horizontally
- Check for memory leaks

---

## Maintenance

### Updates

```bash
# Pull latest images
docker-compose pull

# Restart services
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head
```

### Log Rotation

Configure in `docker-compose.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```
