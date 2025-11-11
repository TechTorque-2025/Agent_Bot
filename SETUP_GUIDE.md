# Agent Bot - Setup and Quick Start Guide

## Current Status (Fixed)

✅ **All import errors have been resolved**
✅ **Dependencies installed correctly**
✅ **Code adapted for LangChain 0.1.6 compatibility**

## What Was Fixed

### 1. LangChain Version Mismatch
- **Problem**: Code was using `create_tool_calling_agent` from newer LangChain (1.0+), but virtualenv had incompatible version
- **Solution**: 
  - Downgraded to `langchain==0.1.6` which has `AgentExecutor` and `initialize_agent`
  - Updated `services/agent_core.py` to use `initialize_agent()` with `AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION`

### 2. Missing Dependencies
- **Problem**: Missing `sentence-transformers`, `pinecone-client`, `torch`, and other ML libraries
- **Solution**: 
  - Created `requirements.txt` with all dependencies pinned
  - Installed complete dependency tree (~3GB+ with PyTorch)

### 3. Missing Singleton Function
- **Problem**: `get_document_service()` was not defined in `services/document.py`
- **Solution**: Added singleton pattern getter function at end of file

### 4. Missing Environment Configuration
- **Problem**: No `.env` file with API keys
- **Solution**: Created `.env.example` template

## Next Steps to Start the Application

### Step 1: Set Up Environment Variables

Create a `.env` file in the Agent_Bot directory:

```bash
cd /home/randitha/Desktop/IT/UoM/TechTorque-2025/Agent_Bot
cp .env.example .env
```

Then edit `.env` and add your actual API keys:

```bash
# Required keys:
GOOGLE_API_KEY=your_actual_google_gemini_api_key
PINECONE_API_KEY=your_actual_pinecone_api_key
```

### Step 2: Start the Application

```bash
# Activate virtualenv (if not already active)
source .venv/bin/activate

# Or directly run with virtualenv python:
/home/randitha/Desktop/IT/UoM/TechTorque-2025/Agent_Bot/.venv/bin/python main.py
```

### Step 3: Access the API

Once running, the service will be available at:
- **Base URL**: http://localhost:8091
- **API Endpoint**: http://localhost:8091/api/v1/ai/chat
- **Health Check**: http://localhost:8091/health
- **API Docs**: http://localhost:8091/docs

## Where to Get API Keys

### Google Gemini API Key
1. Go to: https://makersuite.google.com/app/apikey
2. Create a new API key for Gemini
3. Copy the key to your `.env` file

### Pinecone API Key
1. Sign up at: https://www.pinecone.io/
2. Create a free "Starter" project
3. Go to "API Keys" in dashboard
4. Create/copy your API key
5. Create an index named `techtorque-kb` with dimension `384`

## Files Modified

- `services/agent_core.py` - Updated agent initialization for LangChain 0.1.6
- `services/document.py` - Added missing singleton getter function
- `requirements.txt` - Created with all dependencies
- `.env.example` - Created configuration template

## Commit Your Changes

```bash
cd /home/randitha/Desktop/IT/UoM/TechTorque-2025/Agent_Bot
git add services/agent_core.py services/document.py requirements.txt .env.example
git commit -m "fix: Resolve LangChain import errors and add dependencies

- Adapt agent_core.py for LangChain 0.1.6 API (use initialize_agent)
- Add missing get_document_service() singleton function
- Create requirements.txt with pinned dependencies
- Add .env.example configuration template"
```

## Testing Without API Keys (Optional)

If you don't have API keys yet but want to test imports, you can temporarily set dummy values:

```bash
export GOOGLE_API_KEY=dummy_key_for_testing
export PINECONE_API_KEY=dummy_key_for_testing
python main.py
```

The app will start but fail when actually trying to use the APIs. This is useful for verifying all imports work.

## Architecture Notes

This Agent Bot is part of a microservices architecture:
- **Port**: 8091 (Agent Bot service)
- **Dependencies**: Authentication, Vehicle, Project, Time Logging, Appointment services
- **Features**: 
  - LangChain-based AI agent with tool calling
  - RAG (Retrieval Augmented Generation) with Pinecone vector store
  - Integration with TechTorque backend microservices
  - Google Gemini 2.5 Flash model

## Troubleshooting

### Import Errors
✅ Fixed - LangChain version now matches code expectations

### "Module not found" for sentence_transformers
✅ Fixed - All ML dependencies now installed

### "GOOGLE_API_KEY not found"
⚠️  **Action Required**: Create `.env` file with actual API keys

### Large Download Size
ℹ️  PyTorch and ML models are large (~3GB). This is normal for AI applications.
