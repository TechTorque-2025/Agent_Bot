import httpx
import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from config.settings import settings
from models.chat import UserContext, VehicleInfo

logger = logging.getLogger(__name__)

class MicroserviceClient:
    """
    Client for ASYNCHRONOUS calls to various microservices.
    
    NOTE: The client uses httpx.AsyncClient internally to support the 
    async agent tools in agent_tools.py.
    """

    def __init__(self):
        # Initialize an AsyncClient once per instance
        self._async_client = httpx.AsyncClient(timeout=5.0) 
        self.auth_url = settings.AUTHENTICATION_SERVICE_URL
        self.vehicle_url = settings.VEHICLE_SERVICE_URL
        self.project_url = settings.PROJECT_SERVICE_URL
        
        # FIX: Added required microservice URLs
        self.appointment_url = settings.APPOINTMENT_SERVICE_URL
        self.time_log_url = settings.TIME_LOGGING_SERVICE_URL

    async def _make_get_request(self, url: str, token: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Internal helper for making async authenticated GET requests."""
        headers = {"Authorization": f"Bearer {token}"}
        try:
            # FIX: Use async client and await
            response = await self._async_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as errh:
            logger.error(f"HTTP Error {errh.response.status_code} from {url}: {errh.response.text}")
            return {"error": f"HTTP Error {errh.response.status_code}", "status_code": errh.response.status_code}
        except httpx.RequestError as errc:
            logger.error(f"Request Error to {url}: {errc}")
            return {"error": "Microservice Unreachable", "status_code": 503}
        except Exception as e:
            logger.error(f"Unexpected Error from {url}: {e}")
            return {"error": str(e), "status_code": 500}

    # --- Methods used by Agent Core (Called Synchronously, requires wrapper) ---

    def get_user_context(self, token: str) -> UserContext:
        """Retrieves user profile and vehicles. Synchronous entry point for agent_core."""
        # FIX: Use wrapper to run the async logic synchronously without blocking the FastAPI event loop
        return asyncio.run(self._async_get_user_context(token))

    async def _async_get_user_context(self, token: str) -> UserContext:
        """Retrieves user profile and vehicles (ASYNC helper)."""
        
        # 1. Get User Profile (/auth/me endpoint)
        user_data = await self._make_get_request(f"{self.auth_url}/me", token)
        if "error" in user_data:
            return UserContext(user_id="anonymous", full_name="Guest", role="PUBLIC", vehicles=[])
        
        # 2. Get User Vehicles (/vehicles endpoint)
        vehicle_data = await self._make_get_request(f"{self.vehicle_url}", token)
        vehicles = []
        if isinstance(vehicle_data, list):
            vehicles = [
                VehicleInfo(
                    id=v.get("vehicleId", v.get("id", "")),
                    make=v.get("make", ""),
                    model=v.get("model", ""),
                    license_plate=v.get("licensePlate", "")
                ) for v in vehicle_data if isinstance(v, dict)
            ]
        
        return UserContext(
            user_id=user_data.get("id") or user_data.get("userId", "unknown"),
            full_name=user_data.get("fullName") or user_data.get("username", "unknown"),
            role=user_data.get("role", "CUSTOMER"),
            vehicles=vehicles
        )

    # --- Methods used by Agent Tools (ASYNC) ---

    async def get_active_services(self, token: str) -> List[Dict[str, Any]]:
        """Retrieves active services and projects for the current user."""
        
        services_data = await self._make_get_request(f"{self.project_url}", token)
        
        active_items = []
        if isinstance(services_data, list):
            for item in services_data:
                 if item.get('status') in ['IN_PROGRESS', 'REQUESTED', 'APPROVED']:
                     active_items.append({
                         "type": "project" if item.get('isProject') else "service",
                         "id": item.get('projectId', item.get('serviceId', 'N/A')),
                         "status": item.get('status'),
                         "vehicle_model": item.get('vehicle', {}).get('model', 'N/A')
                     })

        return active_items

    async def get_appointment_slots(self, date: str, service_type: str, token: str) -> Dict[str, Any]:
        """FIX: Implements the ASYNC method called by check_appointment_slots_tool."""
        url = f"{self.appointment_url}/availability"
        params = {"date": date, "serviceType": service_type}
        data = await self._make_get_request(url, token, params)
        # Assuming the service returns the data directly or returns a dict with 'available_slots' key
        return data

    @staticmethod
    def _parse_logs_response(data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Safely parses the logs response, assuming it's a list or nested list/dict."""
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'logs' in data and isinstance(data['logs'], list):
            return data['logs']
        return []

    async def get_time_logs_for_service(self, service_id: str, token: str) -> List[Dict[str, Any]]:
        """
        FIX: Implements the ASYNC method called by get_last_work_log_tool.
        """
        url = f"{self.time_log_url}/{service_id}"
        data = await self._make_get_request(url, token)
        
        if data.get("error"):
             logger.warning(f"Error fetching logs for {service_id}: {data['error']}")
             return []
        
        return self._parse_logs_response(data)


# Singleton instance
_microservice_client_instance = None
def get_microservice_client() -> MicroserviceClient:
    global _microservice_client_instance
    if _microservice_client_instance is None:
        _microservice_client_instance = MicroserviceClient()
    return _microservice_client_instance