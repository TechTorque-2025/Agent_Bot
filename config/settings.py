# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # --- LLM & RAG API Keys ---
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "techtorque-kb")
    
    # --- Gemini Model & RAG Settings ---
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash") # Using 2.5 flash
    RAG_CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", 500))
    RAG_CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", 50))
    RAG_MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", 2000))

    # --- Microservice URLs (My Original Contribution) ---
    BASE_SERVICE_URL = os.getenv("BASE_SERVICE_URL", "http://localhost:8080/api/v1")
    AUTHENTICATION_SERVICE_URL = os.getenv("AUTHENTICATION_SERVICE_URL", BASE_SERVICE_URL + "/auth")
    VEHICLE_SERVICE_URL = os.getenv("VEHICLE_SERVICE_URL", BASE_SERVICE_URL + "/vehicles")
    PROJECT_SERVICE_URL = os.getenv("PROJECT_SERVICE_URL", BASE_SERVICE_URL + "/jobs")
    TIME_LOGGING_SERVICE_URL = os.getenv("TIME_LOGGING_SERVICE_URL", BASE_SERVICE_URL + "/logs")

    # --- Appointment Service (Used by both Agent and RAG) ---
    APPOINTMENT_SERVICE_URL = os.getenv("APPOINTMENT_SERVICE_URL", BASE_SERVICE_URL + "/appointments")

    # --- Server ---
    PORT = int(os.getenv("PORT", 8091))
    
settings = Settings()