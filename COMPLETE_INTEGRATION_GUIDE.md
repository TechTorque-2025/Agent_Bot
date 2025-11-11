# Agent Bot - Complete Integration Guide

## 🎯 Overview

This document provides a complete guide for integrating the Agent_Bot service into the TechTorque microservices ecosystem with full CI/CD and Kubernetes deployment.

## ✅ What Has Been Created

### 1. Agent_Bot Repository
```
Agent_Bot/
├── .github/workflows/
│   ├── build.yaml          ✅ NEW - Build & push Docker image
│   └── deploy.yaml         ✅ NEW - Deploy to Kubernetes
├── .dockerignore           ✅ NEW - Optimize Docker builds
├── Dockerfile              ✅ NEW - Python FastAPI container
├── requirements.txt        ✅ UPDATED - Clean dependencies
├── IMPLEMENTATION_SUMMARY.md     ✅ NEW - This implementation
├── CICD_K8S_DEPLOYMENT.md       ✅ NEW - Detailed guide
└── QUICK_REFERENCE.md           ✅ NEW - Quick commands
```

### 2. k8s-config Repository
```
k8s-config/
├── k8s/
│   ├── configmaps/
│   │   └── agent-bot-configmap.yaml    ✅ NEW
│   ├── secrets/
│   │   └── agent-bot-secrets.template.yaml    ✅ NEW
│   └── services/
│       ├── agent-bot-deployment.yaml   ✅ NEW
│       └── gateway-deployment.yaml     ✅ UPDATED - Added Agent Bot URL
└── create-all-secrets.sh   ✅ UPDATED - Added Agent Bot secrets
```

### 3. API Gateway
```
API_Gateway/
└── config.yaml             ✅ UPDATED - Configured AI service routing
```

## 🔧 Configuration Changes Summary

### API Gateway Updates

**config.yaml** - Updated AI service routing:
```yaml
- name: "ai"
  path_prefix: "/api/v1/ai/"
  target_url: "http://localhost:8091"  # Changed from 8089
  strip_prefix: "/api/v1/ai"
  auth_required: true
  env_var: "AGENT_BOT_SERVICE_URL"     # Added env var
```

**gateway-deployment.yaml** - Added service URL:
```yaml
- name: "AGENT_BOT_SERVICE_URL"
  value: "http://agent-bot-service"
```

### ConfigMap Configuration

**Service URLs**: All configured to use API Gateway
- `BASE_SERVICE_URL: "http://api-gateway/api/v1"`
- `AUTHENTICATION_SERVICE_URL: "http://api-gateway/api/v1/auth"`
- `VEHICLE_SERVICE_URL: "http://api-gateway/api/v1/vehicles"`
- `PROJECT_SERVICE_URL: "http://api-gateway/api/v1/jobs"`
- `TIME_LOGGING_SERVICE_URL: "http://api-gateway/api/v1/logs"`
- `APPOINTMENT_SERVICE_URL: "http://api-gateway/api/v1/appointments"`

**AI Configuration**:
- `GEMINI_MODEL: "gemini-2.5-flash"`
- `PINECONE_INDEX_NAME: "techtorque-kb"`
- `PINECONE_ENVIRONMENT: "us-east-1-aws"`

**RAG Configuration**:
- `RAG_CHUNK_SIZE: "500"`
- `RAG_CHUNK_OVERLAP: "50"`
- `MAX_CONTEXT_LENGTH: "2000"`

## 🚀 Deployment Instructions

### Step 1: Prepare External Services

#### Google Gemini API
1. Visit https://makersuite.google.com/app/apikey
2. Create a new API key
3. Save the key securely

#### Pinecone
1. Visit https://app.pinecone.io/
2. Create account if needed
3. Create a new index:
   - Name: `techtorque-kb`
   - Dimensions: 384 (for sentence-transformers/all-MiniLM-L6-v2)
   - Metric: cosine
   - Environment: us-east-1-aws
4. Get your API key

### Step 2: Create Kubernetes Secrets

```bash
cd k8s-config

# Option 1: Use the automated script
./create-all-secrets.sh
# When prompted for "agent-bot", enter:
# - Google Gemini API key
# - Pinecone API key

# Option 2: Manual creation
kubectl create secret generic agent-bot-secrets \
  --from-literal=GOOGLE_API_KEY='your-gemini-key-here' \
  --from-literal=PINECONE_API_KEY='your-pinecone-key-here' \
  --namespace=default
```

### Step 3: Apply Kubernetes Configurations

```bash
cd k8s-config

# Apply ConfigMap
kubectl apply -f k8s/configmaps/agent-bot-configmap.yaml

# Apply Deployment (includes Service)
kubectl apply -f k8s/services/agent-bot-deployment.yaml

# Update API Gateway (to include Agent Bot URL)
kubectl apply -f k8s/services/gateway-deployment.yaml
```

### Step 4: Verify Deployment

```bash
# Check pods are running
kubectl get pods -l app=agent-bot-service

# Check service is created
kubectl get svc agent-bot-service

# View logs
kubectl logs -l app=agent-bot-service --tail=50

# Check health
kubectl run -it --rm test --image=curlimages/curl --restart=Never -- \
  curl http://agent-bot-service/health
```

### Step 5: Trigger CI/CD Pipeline

```bash
cd Agent_Bot

# Add and commit changes
git add .
git commit -m "feat: Add CI/CD and K8s configuration for Agent Bot"

# Push to trigger workflows
git push origin devOps
# OR
git push origin main
```

### Step 6: Monitor Deployment

```bash
# Watch GitHub Actions
# Visit: https://github.com/TechTorque-2025/Agent_Bot/actions

# Watch Kubernetes deployment
kubectl get pods -l app=agent-bot-service -w

# Check rollout status
kubectl rollout status deployment/agent-bot-deployment

# View recent logs
kubectl logs -l app=agent-bot-service --tail=100 -f
```

## 🧪 Testing

### Test 1: Health Check (Internal)
```bash
kubectl run -it --rm test --image=curlimages/curl --restart=Never -- \
  curl http://agent-bot-service/health
```

Expected response:
```json
{"status": "healthy"}
```

### Test 2: Service Info
```bash
kubectl run -it --rm test --image=curlimages/curl --restart=Never -- \
  curl http://agent-bot-service/
```

Expected response:
```json
{
  "service": "TechTorque Unified AI Agent",
  "status": "running",
  "model": "gemini-2.5-flash",
  "api_endpoints": "/api/v1/ai/chat",
  "rag_endpoints": "/api/v1/ai/rag/status"
}
```

### Test 3: Chat Endpoint (Via Gateway)
```bash
# Get a valid JWT token first
TOKEN=$(curl -X POST http://api-gateway-service/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.token')

# Test chat endpoint
curl -X POST http://api-gateway-service/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "message": "Hello, what can you help me with?",
    "session_id": "test-session-123"
  }'
```

### Test 4: Check from Frontend
Once frontend is updated, test from browser:
```javascript
// In browser console
fetch('http://your-domain.com/api/v1/ai/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + localStorage.getItem('token')
  },
  body: JSON.stringify({
    message: 'Hello',
    session_id: 'browser-test'
  })
})
.then(r => r.json())
.then(console.log)
```

## 🔍 Troubleshooting

### Issue 1: Pods Not Starting

**Symptoms:**
```bash
kubectl get pods -l app=agent-bot-service
# Shows: CrashLoopBackOff or ImagePullBackOff
```

**Solutions:**

1. **ImagePullBackOff:**
   ```bash
   # Check image exists
   docker pull ghcr.io/techtorque-2025/agent_bot:latest
   
   # Verify image name in deployment
   kubectl describe deployment agent-bot-deployment
   ```

2. **CrashLoopBackOff:**
   ```bash
   # Check logs for errors
   kubectl logs -l app=agent-bot-service --tail=100
   
   # Common issues:
   # - Missing API keys in secrets
   # - Invalid API keys
   # - Pinecone index doesn't exist
   ```

3. **Verify Secrets:**
   ```bash
   kubectl get secret agent-bot-secrets
   kubectl describe secret agent-bot-secrets
   
   # Recreate if needed
   kubectl delete secret agent-bot-secrets
   ./create-all-secrets.sh
   ```

### Issue 2: Health Check Failing

**Symptoms:**
```bash
kubectl get pods -l app=agent-bot-service
# Shows: Pods restarting frequently
```

**Solutions:**
```bash
# Check health endpoint directly
kubectl exec -it <pod-name> -- curl localhost:8091/health

# Check if port is correct
kubectl get pod <pod-name> -o yaml | grep containerPort

# Increase initial delay if startup is slow
kubectl edit deployment agent-bot-deployment
# Update: initialDelaySeconds: 60
```

### Issue 3: Can't Reach Other Services

**Symptoms:**
- Chat endpoint returns errors about unable to reach services

**Solutions:**
```bash
# Verify API Gateway is running
kubectl get svc api-gateway-service

# Check if Agent Bot can reach gateway
kubectl exec -it <agent-bot-pod> -- curl http://api-gateway-service/health

# Verify service URLs in ConfigMap
kubectl get configmap agent-bot-config -o yaml

# Check Agent Bot logs for connection errors
kubectl logs -l app=agent-bot-service | grep -i error
```

### Issue 4: GitHub Actions Failing

**Build Workflow Fails:**
```bash
# Check build.yaml syntax
cd Agent_Bot
cat .github/workflows/build.yaml

# Test Docker build locally
docker build -t agent-bot:test .

# Check workflow logs in GitHub Actions UI
```

**Deploy Workflow Fails:**
```bash
# Verify secrets are set in GitHub
# Settings > Secrets and variables > Actions
# Required:
# - REPO_ACCESS_TOKEN
# - KUBE_CONFIG_DATA

# Check workflow logs for specific errors
```

### Issue 5: Gemini API Errors

**Symptoms:**
- Chat returns errors about API quota or authentication

**Solutions:**
```bash
# Verify API key is correct
kubectl get secret agent-bot-secrets -o jsonpath='{.data.GOOGLE_API_KEY}' | base64 -d

# Test API key manually
curl https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: YOUR_API_KEY" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'

# Check quota limits in Google AI Studio
```

### Issue 6: Pinecone Errors

**Symptoms:**
- RAG queries failing or returning errors

**Solutions:**
```bash
# Verify Pinecone index exists
# Visit: https://app.pinecone.io/

# Check index name matches ConfigMap
kubectl get configmap agent-bot-config -o yaml | grep PINECONE_INDEX_NAME

# Verify API key
kubectl get secret agent-bot-secrets -o jsonpath='{.data.PINECONE_API_KEY}' | base64 -d

# Check embedding dimension matches (should be 384)
```

## 📊 Monitoring

### Key Metrics

```bash
# Pod status
kubectl get pods -l app=agent-bot-service

# Resource usage
kubectl top pods -l app=agent-bot-service

# Deployment status
kubectl get deployment agent-bot-deployment

# Service endpoints
kubectl get endpoints agent-bot-service

# Recent events
kubectl get events --sort-by='.lastTimestamp' | grep agent-bot
```

### Logs

```bash
# All logs
kubectl logs -l app=agent-bot-service --all-containers=true

# Follow logs
kubectl logs -l app=agent-bot-service -f

# Logs from specific pod
kubectl logs <pod-name>

# Previous logs (if pod crashed)
kubectl logs <pod-name> --previous

# Logs with timestamps
kubectl logs -l app=agent-bot-service --timestamps=true
```

### Performance

```bash
# Check response times
kubectl exec -it <any-pod> -- time curl http://agent-bot-service/health

# Check concurrent connections
kubectl describe svc agent-bot-service

# Monitor resource usage over time
watch kubectl top pods -l app=agent-bot-service
```

## 🔄 Updating the Service

### Update Code Only
```bash
cd Agent_Bot
# Make changes
git add .
git commit -m "feat: your changes"
git push origin main
# CI/CD will auto-deploy
```

### Update Configuration
```bash
cd k8s-config

# Edit ConfigMap
kubectl edit configmap agent-bot-config
# OR
vim k8s/configmaps/agent-bot-configmap.yaml
kubectl apply -f k8s/configmaps/agent-bot-configmap.yaml

# Restart pods to pick up changes
kubectl rollout restart deployment/agent-bot-deployment
```

### Update Secrets
```bash
cd k8s-config

# Delete old secret
kubectl delete secret agent-bot-secrets

# Create new secret
./create-all-secrets.sh

# Restart pods
kubectl rollout restart deployment/agent-bot-deployment
```

### Scale Service
```bash
# Scale up
kubectl scale deployment agent-bot-deployment --replicas=3

# Scale down
kubectl scale deployment agent-bot-deployment --replicas=1

# Auto-scale (if HPA configured)
kubectl autoscale deployment agent-bot-deployment --min=2 --max=5 --cpu-percent=80
```

## 🎯 Next Steps

### 1. Frontend Integration
- Update frontend to call `/api/v1/ai/chat`
- Add chat UI component
- Handle streaming responses (if implemented)

### 2. Documentation
- Add API documentation to main README
- Create user guide for AI features
- Document RAG document ingestion process

### 3. Monitoring & Alerts
- Set up Prometheus metrics
- Configure Grafana dashboards
- Create alerts for:
  - Pod restarts
  - High response times
  - API quota limits
  - Error rates

### 4. Performance Optimization
- Implement response caching
- Add request rate limiting
- Optimize embedding generation
- Consider GPU acceleration for ML models

### 5. Security Enhancements
- Implement request validation
- Add rate limiting per user
- Audit API key usage
- Set up secret rotation

## 📚 Related Documentation

- [Agent Bot README](./README.md) - Service overview
- [CI/CD Deployment Guide](./CICD_K8S_DEPLOYMENT.md) - Detailed deployment info
- [Quick Reference](./QUICK_REFERENCE.md) - Command cheatsheet
- [Implementation Summary](./IMPLEMENTATION_SUMMARY.md) - What was created

## ✅ Pre-Deployment Checklist

- [ ] Google Gemini API key obtained
- [ ] Pinecone account created and index set up
- [ ] Kubernetes secrets created
- [ ] ConfigMap applied
- [ ] API Gateway updated and redeployed
- [ ] GitHub secrets configured (REPO_ACCESS_TOKEN, KUBE_CONFIG_DATA)
- [ ] Docker image builds successfully
- [ ] Workflows tested in GitHub Actions
- [ ] Deployment successful in Kubernetes
- [ ] Health checks passing
- [ ] Service accessible from API Gateway
- [ ] End-to-end test successful

## 🎉 Success Criteria

Your Agent Bot deployment is successful when:

1. ✅ GitHub Actions workflows run without errors
2. ✅ Docker image exists in GHCR: `ghcr.io/techtorque-2025/agent_bot:latest`
3. ✅ Kubernetes pods are running: `kubectl get pods -l app=agent-bot-service`
4. ✅ Health check returns 200: `curl http://agent-bot-service/health`
5. ✅ Service info endpoint works: `curl http://agent-bot-service/`
6. ✅ Chat endpoint responds: `curl http://api-gateway-service/api/v1/ai/chat`
7. ✅ No errors in pod logs: `kubectl logs -l app=agent-bot-service`
8. ✅ Gateway routes correctly to Agent Bot
9. ✅ Authentication works via gateway
10. ✅ AI responses are generated successfully

---

**Status**: ✅ Ready for deployment  
**Last Updated**: 2025-11-12  
**Version**: 1.0.0
