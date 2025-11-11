# 🤖 TechTorque Unified AI Agent / RAG Service

The `Agent_Bot` service is the **intelligence and interaction layer** of the TechTorque platform. It combines two critical AI functionalities:

1.  **AI Agent (Tool Use):** Uses advanced reasoning to perform real-time actions against microservices (e.g., checking appointment slots, viewing user vehicle status).
2.  **RAG (Knowledge Retrieval):** Uses a Vector Database (Pinecone) and a local embedding model to answer non-real-time questions based on structured knowledge documents (e.g., "What is your warranty policy?").

Built with **Python**, **FastAPI**, and **Gemini (via LangChain)**, this service implements the `/api/v1/ai/chat` endpoint.

---

## 🚀 Setup and Local Development

### **Prerequisites**

*   **Python 3.10+**
*   **External Microservices:** The `Authentication`, `Appointment_Service`, `Vehicle_Service`, and `Project_Service` must be running.
*   **Cloud Services:** A **Gemini API Key** and a **Pinecone Account/API Key** are required for RAG functionality.

### **1. Environment Setup**

1.  **Navigate to the project directory:**
    ```bash
    cd Agent_Bot
    ```
2.  **Activate the virtual environment:**
    ```bash
    source venv/bin/activate  # macOS/Linux
    .\venv\Scripts\activate    # Windows
    ```
3.  **Install dependencies:**
    *(Ensure you run this command inside the active `(venv)` to resolve all LangChain dependencies)*
    ```bash
    pip install -r requirements.txt 
    ```

### **2. Configuration (.env)**

Create a **`.env`** file in the root of the `Agent_Bot` directory and populate it with your specific secrets and URLs.

```dotenv
# --- LLM & RAG Configuration ---
GOOGLE_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY_HERE"
GEMINI_MODEL="gemini-2.5-flash"

PINECONE_API_KEY="YOUR_ACTUAL_PINECONE_API_KEY_HERE"
PINECONE_ENVIRONMENT="us-east-1-aws"
PINECONE_INDEX_NAME="techtorque-kb"

# RAG Configuration Defaults
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
MAX_CONTEXT_LENGTH=2000

# --- Microservice URLs ---
PORT=8091
BASE_SERVICE_URL="http://localhost:8080/api/v1" 

AUTHENTICATION_SERVICE_URL="${BASE_SERVICE_URL}/auth"
VEHICLE_SERVICE_URL="${BASE_SERVICE_URL}/vehicles"
PROJECT_SERVICE_URL="${BASE_SERVICE_URL}/jobs" 
TIME_LOGGING_SERVICE_URL="${BASE_SERVICE_URL}/logs"
APPOINTMENT_SERVICE_URL="${BASE_SERVICE_URL}/appointments"