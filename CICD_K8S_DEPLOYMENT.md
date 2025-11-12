# Agent Bot - CI/CD and Kubernetes Deployment Guide

## Overview

This document describes the CI/CD pipeline and Kubernetes deployment configuration for the Agent_Bot service, which is the AI-powered chatbot and RAG service for the TechTorque platform.

## Architecture

**Service Type**: Python FastAPI microservice  
**Port**: 8091  
**Dependencies**: 
- Google Gemini API (for AI responses)
- Pinecone (for vector storage/RAG)
- Internal microservices (via API Gateway)

## CI/CD Pipeline

### GitHub Actions Workflows

The Agent_Bot uses two GitHub Actions workflows following the same pattern as other TechTorque microservices:

#### 1. Build Workflow (`.github/workflows/build.yaml`)

**Triggers:**
- Push to `main`, `devOps`, or `dev` branches
- Pull requests to these branches

**Jobs:**

1. **build-test**
   - Sets up Python 3.11
   - Installs dependencies from `requirements.txt`
   - Runs linting with flake8 (optional)
   - Tests module imports
   - Caches pip packages for faster builds

2. **build-and-push-docker**
   - Only runs on pushes (not PRs)
   - Builds Docker image from Dockerfile
   - Tags image with commit SHA and `latest`
   - Pushes to GitHub Container Registry (GHCR)
   - Image name: `ghcr.io/techtorque-2025/agent_bot:latest`

#### 2. Deploy Workflow (`.github/workflows/deploy.yaml`)

**Triggers:**
- Runs after successful completion of Build workflow
- Only for `main` and `devOps` branches

**Jobs:**

1. **deploy**
   - Checks out k8s-config repository
   - Updates image tag in `agent-bot-deployment.yaml`
   - Applies configuration to Kubernetes cluster
   - Monitors rollout status

### Docker Configuration

**Dockerfile highlights:**
- Base image: `python:3.11-slim`
- Installs system dependencies (gcc, g++)
- Uses multi-stage caching for faster builds
- Exposes port 8091
- Includes health check on `/health` endpoint
- Runs with `uvicorn` ASGI server

## Kubernetes Configuration

### Location
All K8s configurations are in the `k8s-config` repository:
- ConfigMap: `k8s/configmaps/agent-bot-configmap.yaml`
- Secrets: `k8s/secrets/agent-bot-secrets.template.yaml`
- Deployment: `k8s/services/agent-bot-deployment.yaml`

### ConfigMap (`agent-bot-config`)

Contains non-sensitive configuration:
- Service URLs (API Gateway endpoints)
- Gemini model settings
- Pinecone configuration (non-sensitive)
- RAG parameters (chunk size, overlap, context length)

### Secrets (`agent-bot-secrets`)

Contains sensitive API keys:
- `GOOGLE_API_KEY`: Google Gemini API key
- `PINECONE_API_KEY`: Pinecone vector database API key

**Creating the secret:**
```bash
# Method 1: Using the automated script
cd k8s-config
./create-all-secrets.sh

# Method 2: Manual creation
kubectl create secret generic agent-bot-secrets \
  --from-literal=GOOGLE_API_KEY='your-gemini-api-key' \
  --from-literal=PINECONE_API_KEY='your-pinecone-api-key' \
  --namespace=default
```

### Deployment Configuration

**Replica count**: 2 (for high availability)

**Resource limits:**
- Memory: 512Mi (request) / 1Gi (limit)
- CPU: 250m (request) / 500m (limit)

**Health checks:**
- Liveness probe: `/health` endpoint (30s initial delay)
- Readiness probe: `/health` endpoint (15s initial delay)

**Service:**
- Type: ClusterIP (internal only)
- Internal port: 80
- Target port: 8091

### API Gateway Integration

The Agent_Bot service is accessible through the API Gateway at:
```
http://api-gateway/api/v1/ai/chat
```

The API Gateway should be configured to route `/api/v1/ai/*` requests to `http://agent-bot-service:80`.

## Deployment Process

### Prerequisites

1. **GitHub Secrets** (Organization level):
   - `REPO_ACCESS_TOKEN`: Personal access token with repo access
   - `KUBE_CONFIG_DATA`: Base64-encoded kubeconfig for K3s cluster

2. **Kubernetes Cluster** (K3s):
   - Running and accessible
   - kubectl configured

3. **API Keys**:
   - Google Gemini API key
   - Pinecone API key and index created

### Initial Setup

1. **Create Kubernetes secrets:**
   ```bash
   cd k8s-config
   ./create-all-secrets.sh
   # Enter API keys when prompted for agent-bot
   ```

2. **Apply ConfigMap:**
   ```bash
   kubectl apply -f k8s/configmaps/agent-bot-configmap.yaml
   ```

3. **Deploy the service:**
   ```bash
   kubectl apply -f k8s/services/agent-bot-deployment.yaml
   ```

### Automated Deployment

Once the initial setup is complete, deployments happen automatically:

1. Developer pushes code to `main` or `devOps` branch
2. Build workflow runs:
   - Tests the application
   - Builds Docker image
   - Pushes to GHCR
3. Deploy workflow runs:
   - Updates K8s manifest with new image tag
   - Applies to cluster
   - Waits for rollout completion

## Verification

### Check Deployment Status
```bash
kubectl get deployments agent-bot-deployment
kubectl get pods -l app=agent-bot-service
kubectl get service agent-bot-service
```

### Check Logs
```bash
# Get pod name
kubectl get pods -l app=agent-bot-service

# View logs
kubectl logs <pod-name>

# Follow logs
kubectl logs -f <pod-name>
```

### Test the Service
```bash
# From within the cluster
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- \
  curl http://agent-bot-service/health

# Through API Gateway
curl http://<api-gateway-url>/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"message": "Hello", "session_id": "test"}'
```

## Troubleshooting

### Common Issues

1. **Image pull errors:**
   - Ensure GITHUB_TOKEN has correct permissions
   - Check image name matches: `ghcr.io/techtorque-2025/agent_bot:latest`

2. **Secret not found:**
   - Run `kubectl get secret agent-bot-secrets`
   - Recreate using `create-all-secrets.sh`

3. **Service not responding:**
   - Check logs: `kubectl logs <pod-name>`
   - Verify API keys are correct in secrets
   - Ensure Pinecone index exists

4. **Health check failures:**
   - Check if port 8091 is accessible
   - Verify dependencies are installed correctly
   - Check application logs for startup errors

### Rollback

To rollback to a previous version:
```bash
# View rollout history
kubectl rollout history deployment/agent-bot-deployment

# Rollback to previous version
kubectl rollout undo deployment/agent-bot-deployment

# Rollback to specific revision
kubectl rollout undo deployment/agent-bot-deployment --to-revision=<revision>
```

## Monitoring

### Key Metrics to Monitor
- Pod restart count
- Memory/CPU usage
- Response time for `/health` endpoint
- Error rates in application logs
- API rate limits (Gemini, Pinecone)

### Scaling

To scale the deployment:
```bash
# Manual scaling
kubectl scale deployment agent-bot-deployment --replicas=3

# Or edit the deployment file and apply
```

## Security Considerations

1. **API Keys**: Never commit real API keys to version control
2. **Secrets**: Use Kubernetes secrets, not environment variables in deployments
3. **Network**: Service is ClusterIP only, not exposed externally
4. **RBAC**: Ensure proper service account permissions

## Differences from Java Microservices

Unlike the Java Spring Boot services, Agent_Bot:
- Uses Python 3.11 instead of Java 17
- No Maven build process
- Uses `uvicorn` instead of Spring Boot embedded Tomcat
- Different dependency management (pip vs Maven)
- Smaller base image but includes ML libraries
- Different health check patterns

## Related Documentation

- [Agent Bot README](../../Agent_Bot/README.md)
- [Authentication Service CI/CD](../../Authentication/.github/workflows/)
- [K8s Ingress Configuration](./k8s/config/INGRESS_NOTES.md)
