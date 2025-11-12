# Agent Bot - Quick Reference

## Service Information
- **Name**: Agent_Bot
- **Type**: Python FastAPI Microservice
- **Port**: 8091
- **API Endpoint**: `/api/v1/ai/chat`

## Quick Commands

### Local Development
```bash
# Navigate to Agent_Bot directory
cd Agent_Bot

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py
# OR
uvicorn main:app --reload --port 8091
```

### Docker
```bash
# Build image
docker build -t agent-bot:latest .

# Run container
docker run -p 8091:8091 --env-file .env agent-bot:latest

# Run with docker-compose (if configured)
docker-compose up agent-bot
```

### Kubernetes
```bash
# Apply configurations (from k8s-config repo)
kubectl apply -f k8s/configmaps/agent-bot-configmap.yaml
kubectl apply -f k8s/services/agent-bot-deployment.yaml

# Check status
kubectl get pods -l app=agent-bot-service
kubectl get svc agent-bot-service

# View logs
kubectl logs -l app=agent-bot-service --tail=100 -f

# Scale
kubectl scale deployment agent-bot-deployment --replicas=3

# Restart
kubectl rollout restart deployment/agent-bot-deployment

# Rollback
kubectl rollout undo deployment/agent-bot-deployment
```

### GitHub Actions
```bash
# Workflows are triggered automatically on push/PR to:
# - main
# - devOps  
# - dev

# View workflow status at:
# https://github.com/TechTorque-2025/Agent_Bot/actions
```

## Environment Variables

### Required (Sensitive)
```bash
GOOGLE_API_KEY=<your-gemini-api-key>
PINECONE_API_KEY=<your-pinecone-api-key>
```

### Required (Non-Sensitive)
```bash
PORT=8091
BASE_SERVICE_URL=http://localhost:8080/api/v1
GEMINI_MODEL=gemini-2.5-flash
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=techtorque-kb
```

### Optional (with defaults)
```bash
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
MAX_CONTEXT_LENGTH=2000
```

## API Endpoints

### Health Check
```bash
curl http://localhost:8091/health
```

### Root
```bash
curl http://localhost:8091/
```

### Chat (Main endpoint)
```bash
curl -X POST http://localhost:8091/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "message": "Hello, how can you help me?",
    "session_id": "test-session-123"
  }'
```

## Troubleshooting

### Import errors
```bash
pip install --upgrade -r requirements.txt
```

### Port already in use
```bash
# Find process using port 8091
lsof -i :8091
# Kill it
kill -9 <PID>
```

### API Key errors
- Verify `.env` file exists in Agent_Bot directory
- Check API keys are valid
- For Pinecone, ensure index is created

### Docker build fails
```bash
# Clean build
docker build --no-cache -t agent-bot:latest .

# Check logs
docker logs <container-id>
```

### K8s pod not starting
```bash
# Check pod status
kubectl describe pod <pod-name>

# Check secrets exist
kubectl get secret agent-bot-secrets
kubectl describe secret agent-bot-secrets

# Check configmap
kubectl get configmap agent-bot-config
kubectl describe configmap agent-bot-config
```

## File Structure
```
Agent_Bot/
├── .github/
│   └── workflows/
│       ├── build.yaml       # Build and push Docker image
│       └── deploy.yaml      # Deploy to K8s
├── config/
│   └── settings.py          # Configuration management
├── models/
│   └── chat.py             # Pydantic models
├── routes/
│   └── chatAgent.py        # FastAPI routes
├── services/
│   ├── agent_core.py       # Main agent logic
│   ├── agent_tools.py      # LangChain tools
│   ├── microservice_client.py  # Service integration
│   ├── rag.py              # RAG implementation
│   ├── vector.py           # Pinecone integration
│   └── embedding.py        # Embedding service
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
├── main.py                 # Application entry point
└── README.md              # Service documentation
```

## Links
- **Repository**: https://github.com/TechTorque-2025/Agent_Bot
- **Container Registry**: ghcr.io/techtorque-2025/agent_bot
- **K8s Config**: https://github.com/TechTorque-2025/k8s-config

## Common Issues

| Issue | Solution |
|-------|----------|
| ModuleNotFoundError | Run `pip install -r requirements.txt` |
| API key invalid | Check `.env` or K8s secrets |
| Can't reach microservices | Verify API Gateway is running |
| Pinecone errors | Ensure index exists and API key is valid |
| Memory errors | Increase K8s resource limits |
| Slow responses | Check Gemini API rate limits |

## Dependencies
- FastAPI
- LangChain
- Google Gemini API
- Pinecone
- sentence-transformers
- httpx

## Notes
- Unlike Java services, this is Python-based
- Uses uvicorn instead of Spring Boot
- Requires external AI services (Gemini, Pinecone)
- No database required (stateless)
- Communicates with other services via API Gateway
