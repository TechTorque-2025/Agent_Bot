# 🤖 TechTorque AI Agent Bot Microservice

The `Agent_Bot` service is the **intelligence layer** of the TechTorque platform. Built with **Python** and **FastAPI**, it uses a **Gemini-powered LangChain Agent** to process natural language queries, execute actions against other microservices, and provide contextual, conversational responses to users.

This service implements the `/api/v1/ai/chat` endpoint, connecting the `Frontend_Web` chat widget to the backend ecosystem.

---

## 🚀 Setup and Local Development

### **Prerequisites**

* **Python 3.10+**
* The following microservices must be running (e.g., via Docker Compose or locally on port 8080): `Authentication`, `Appointment_Service`, `Vehicle_Service`, `Time_Logging_Service`.
* A **Gemini API Key** is required.

### **1. Environment Setup**

1.  **Navigate to the project directory:**
    ```bash
    cd Agent_Bot
    ```
2.  **Create and activate the virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    .\venv\Scripts\activate   # Windows
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt 
    # Or manually:
    # pip install fastapi uvicorn pydantic requests langchain-google-genai python-dotenv
    ```

### **2. Configuration (.env)**

Create a **`.env`** file in the root of the `Agent_Bot` directory and populate it with the following connection details:

```dotenv
# Gemini API Key (Required for the LLM)
GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"

# Base URL for the other services (e.g., API Gateway or direct service ports)
BASE_SERVICE_URL="http://localhost:8080/api/v1" 

# Service URLs - These must match the running Spring Boot/GoLang services
AUTHENTICATION_SERVICE_URL="${BASE_SERVICE_URL}/auth"
APPOINTMENT_SERVICE_URL="${BASE_SERVICE_URL}/appointments"
VEHICLE_SERVICE_URL="${BASE_SERVICE_URL}/vehicles"
PROJECT_SERVICE_URL="${BASE_SERVICE_URL}/jobs" 
TIME_LOGGING_SERVICE_URL="${BASE_SERVICE_URL}/logs"
 File Structure and Purpose
The Agent_Bot microservice is organized to clearly separate concerns related to application setup, LangChain logic, and inter-service communication.
Configuration & Environment

venv/: The isolated Python Virtual Environment containing all project dependencies (FastAPI, LangChain, google-genai, etc.).

.env: Configuration file for local development. Stores sensitive keys (like GEMINI_API_KEY) and endpoints for dependent microservices (e.g., APPOINTMENT_SERVICE_URL). This file is ignored by Git.

.gitignore: Specifies files and folders (e.g., venv/, .env, __pycache__) that Git should ignore and not track.


Application Core & Infrastructure

main.py: The primary application entry point. Initializes FastAPI, loads environment variables, defines the core /api/v1/ai/chat endpoint, and manages the overall request/response flow.

service_clients.py: The service communication layer. Contains helper functions to make authenticated HTTP calls to other microservices (Auth, Appointment, Vehicle, etc.) using their configured URLs.

models.py: Defines the data structures (Pydantic models) used for API requests/responses (e.g., ChatRequest, ChatResponse) and for mapping data retrieved from other microservices (e.g., Vehicle, UserContext).
Agent Logic (LangChain)

agent_core.py: The Agent's Brain. Initializes the Gemini LLM, defines the Agent's system prompt and rules, and assembles the final LangChain AgentExecutor with all defined tools.

tools.py: Defines the external functions (Tools) that the LLM can call. These functions map natural language intents (e.g., "check status") to the concrete Python code that executes them.


session_manager.py: Manages the conversational state. Contains logic (currently using an in-memory placeholder) to load, update, and save the chat history using the unique session_id.
