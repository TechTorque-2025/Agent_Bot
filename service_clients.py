# Agent_Bot/service_clients.py
import requests
import os
from .models import UserContext
from typing import List, Dict, Any

# URLs loaded from .env
BASE_URL = os.getenv("BASE_SERVICE_URL")
AUTH_URL = os.getenv("AUTHENTICATION_SERVICE_URL")
APPOINTMENT_URL = os.getenv("APPOINTMENT_SERVICE_URL")
PROJECT_URL = os.getenv("PROJECT_SERVICE_URL")
TIME_LOG_URL = os.getenv("TIME_LOGGING_SERVICE_URL")
VEHICLE_URL = os.getenv("VEHICLE_SERVICE_URL")

def make_get_request(url: str, token: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Helper function to make authenticated GET requests."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.HTTPError as errh:
        return {"error": f"HTTP Error: {errh}", "status_code": response.status_code}
    except requests.exceptions.ConnectionError as errc:
        return {"error": "Connection Error: Microservice is unreachable.", "status_code": 503}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}", "status_code": 500}

# --- CONTEXT RETRIEVAL ---
def get_user_context(token: str) -> UserContext:
    """Retrieves user profile and vehicles in a single call."""
    
    # 1. Get User Profile (using /me endpoint from AuthController)
    user_data = make_get_request(f"{AUTH_URL}/me", token)
    if "error" in user_data:
        # In a real app, this should throw an auth error
        return UserContext(user_id="ERROR", full_name="User", vehicles=[])
    
    # 2. Get User Vehicles (using GET /vehicles from VehicleController)
    vehicle_data = make_get_request(f"{VEHICLE_URL}", token)
    vehicles = [v for v in vehicle_data if isinstance(v, dict)]
    
    return UserContext(
        user_id=user_data.get("id"), # Assuming 'id' is the UUID from UserDto
        full_name=user_data.get("username"), 
        vehicles=vehicles
    )

# --- TOOL IMPLEMENTATION FUNCTIONS ---
# Tool 1: Check Availability (GET /appointments/availability)
def client_check_availability(date: str, service_type: str, token: str) -> Dict[str, Any]:
    """Calls Appointment Service to check availability (Public endpoint, but we pass token for safety)."""
    return make_get_request(
        url=f"{APPOINTMENT_URL}/availability", 
        token=token,
        params={"date": date, "serviceType": service_type, "duration": 60} # Hardcode 60 min for prototype
    )

# Tool 2: Get Active Services (GET /services or /projects)
def client_get_active_services(token: str) -> List[Dict[str, Any]]:
    """Calls Project Service to get all active services/projects for the current user (using /services and /projects)."""
    # NOTE: Your controllers don't have a GET endpoint to list ALL services/projects 
    # for a customer by a status, so we will use the base /projects and /services
    
    # This assumes the token holder is a CUSTOMER
    services = make_get_request(f"{PROJECT_URL}/services?status=IN_PROGRESS", token)
    projects = make_get_request(f"{PROJECT_URL}/projects?status=IN_PROGRESS", token)

    # Filter out errors and combine
    active_items = []
    if not services.get("error"):
         active_items.extend([{"type": "service", "id": s.get("id"), "status": s.get("status")} for s in services if isinstance(s, dict)])
    if not projects.get("error"):
         active_items.extend([{"type": "project", "id": p.get("id"), "status": p.get("status")} for p in projects if isinstance(p, dict)])

    return active_items

# Tool 3: Get Time Logs (GET /time-logs/service/{serviceId})
def client_get_time_logs(service_id: str, token: str) -> List[Dict[str, Any]]:
    """Calls Time Logging Service to get logs for a specific service/job."""
    # Based on TimeLoggingController: @GetMapping("/service/{serviceId}")
    return make_get_request(f"{TIME_LOG_URL}/service/{service_id}", token)