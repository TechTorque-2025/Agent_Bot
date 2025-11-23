import httpx
import os
import logging
import asyncio
import jwt
from typing import List, Dict, Any, Optional, Tuple
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
        # Normalize and sanitize URLs (strip whitespace and trailing slashes as needed)
        self.auth_url = (settings.AUTHENTICATION_SERVICE_URL or "").strip()
        self.vehicle_url = (settings.VEHICLE_SERVICE_URL or "").strip()
        self.project_url = (settings.PROJECT_SERVICE_URL or "").strip()
        
        # FIX: Added required microservice URLs
        self.appointment_url = settings.APPOINTMENT_SERVICE_URL
        self.time_log_url = settings.TIME_LOGGING_SERVICE_URL

    def _extract_user_from_token(self, token: str) -> Tuple[str, str]:
        """
        Extract username and roles from JWT token.
        Returns (username, roles_csv_string)
        """
        try:
            # Decode without verification (we trust our own tokens)
            payload = jwt.decode(token, options={"verify_signature": False})
            username = payload.get("sub", "")
            
            # Extract roles - they might be in different formats
            roles = payload.get("roles", [])
            if isinstance(roles, list):
                # Remove ROLE_ prefix if present
                cleaned_roles = [r.replace("ROLE_", "") for r in roles]
                roles_str = ",".join(cleaned_roles)
            elif isinstance(roles, str):
                roles_str = roles.replace("ROLE_", "")
            else:
                roles_str = ""
                
            logger.debug(f"Extracted from JWT - username: {username}, roles: {roles_str}")
            return username, roles_str
        except Exception as e:
            logger.warning(f"Failed to extract user from token: {e}")
            return "", ""

    async def _make_get_request(self, url: str, token: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Internal helper for making async authenticated GET requests."""
        headers = {"Authorization": f"Bearer {token}"}
        
        # Add X-User headers for direct service calls
        username, roles = self._extract_user_from_token(token)
        if username:
            headers["X-User-Subject"] = username
            headers["X-User-Roles"] = roles
            
        # defensive trimming - remove accidental spaces
        url = (url or "").strip()
        logger.debug(f"Making GET request to: {url} params={params}")
        try:
            response = await self._async_client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as errh:
            # Detailed error body may be helpful for callers - attempt to parse JSON
            status = errh.response.status_code
            body = None
            try:
                body = errh.response.json()
            except Exception:
                body = errh.response.text or None

            logger.error(f"HTTP Error {status} from {url}: {body}")

            # Return underlying error body if available, but keep a consistent shape
            result = {"status_code": status}
            if isinstance(body, dict):
                # merge error body and preserve status_code
                result.update(body)
            else:
                result["error"] = body or f"HTTP Error {status}"

            return result
        except httpx.RequestError as errc:
            logger.error(f"Request Error to {url}: {errc}")
            return {"error": "Microservice Unreachable", "status_code": 503}
        except Exception as e:
            logger.error(f"Unexpected Error from {url}: {e}")
            return {"error": str(e), "status_code": 500}

    async def _make_post_request(self, url: str, token: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Internal helper for making async authenticated POST requests."""
        headers = {"Authorization": f"Bearer {token}"}
        
        # Add X-User headers for direct service calls
        username, roles = self._extract_user_from_token(token)
        if username:
            headers["X-User-Subject"] = username
            headers["X-User-Roles"] = roles
            
        try:
            response = await self._async_client.post(url, json=data, headers=headers)
            if response.is_success:
                return response.json()
            try:
                return response.json()
            except:
                 return {"error": f"HTTP Error {response.status_code}", "status_code": response.status_code}
        except Exception as e:
            logger.error(f"POST Error to {url}: {e}")
            return {"error": str(e), "status_code": 500}

    async def _make_put_request(self, url: str, token: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Internal helper for making async authenticated PUT requests."""
        headers = {"Authorization": f"Bearer {token}"}
        
        # Add X-User headers for direct service calls
        username, roles = self._extract_user_from_token(token)
        if username:
            headers["X-User-Subject"] = username
            headers["X-User-Roles"] = roles
            
        try:
            response = await self._async_client.put(url, json=data, headers=headers)
            if response.is_success:
                return response.json()
            try:
                return response.json()
            except:
                 return {"error": f"HTTP Error {response.status_code}", "status_code": response.status_code}
        except Exception as e:
            logger.error(f"PUT Error to {url}: {e}")
            return {"error": str(e), "status_code": 500}

    async def _make_delete_request(self, url: str, token: str) -> Dict[str, Any]:
        """Internal helper for making async authenticated DELETE requests."""
        headers = {"Authorization": f"Bearer {token}"}
        
        # Add X-User headers for direct service calls
        username, roles = self._extract_user_from_token(token)
        if username:
            headers["X-User-Subject"] = username
            headers["X-User-Roles"] = roles
            
        try:
            response = await self._async_client.delete(url, headers=headers)
            if response.is_success:
                return {"success": True, "status_code": response.status_code}
            try:
                return response.json()
            except:
                 return {"error": f"HTTP Error {response.status_code}", "status_code": response.status_code}
        except Exception as e:
            logger.error(f"DELETE Error to {url}: {e}")
            return {"error": str(e), "status_code": 500}

    # --- Methods used by Agent Core (Called from async context) ---

    async def get_user_context(self, token: str) -> UserContext:
        """Retrieves user profile and vehicles. Async method for agent_core."""
        return await self._async_get_user_context(token)

    async def _async_get_user_context(self, token: str) -> UserContext:
        """Retrieves user profile and vehicles (ASYNC helper)."""
        
        # 1. Get User Profile (/users/me endpoint)
        base_url = self.auth_url.strip().rstrip('/')
        if base_url.endswith('/users'):
            url = f"{base_url}/me"
        else:
            url = f"{base_url}/users/me"
            
        user_data = await self._make_get_request(url, token)
        if "error" in user_data:
            return UserContext(user_id="anonymous", full_name="Guest", role="PUBLIC", vehicles=[])
        
        # 2. Get User Vehicles (/vehicles endpoint)
        url = self.vehicle_url.strip().rstrip('/')
        if not url.endswith("/vehicles"):
            url = f"{url}/vehicles"
        vehicle_data = await self._make_get_request(url, token)
        
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

    # --- New Methods for Enhanced Agent Capabilities ---

    # 1. Appointments
    async def book_appointment(self, appointment_data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Books a new appointment."""
        return await self._make_post_request(self.appointment_url, token, appointment_data)

    async def cancel_appointment(self, appointment_id: str, token: str) -> Dict[str, Any]:
        """Cancels an appointment."""
        url = f"{self.appointment_url}/{appointment_id}"
        return await self._make_delete_request(url, token)

    # 2. Vehicles
    async def get_customer_vehicles(self, token: str) -> List[Dict[str, Any]]:
        """Get all vehicles for the current user."""
        url = self.vehicle_url.strip().rstrip('/')
        if not url.endswith("/vehicles"):
            url = f"{url}/vehicles"
        result = await self._make_get_request(url, token)
        if isinstance(result, list):
            return result
        return []

    async def get_vehicle_details(self, vehicle_id: str, token: str) -> Dict[str, Any]:
        """Get details for a specific vehicle."""
        base_url = self.vehicle_url.strip().rstrip('/')
        if base_url.endswith("/vehicles"):
            url = f"{base_url}/{vehicle_id}"
        else:
            url = f"{base_url}/vehicles/{vehicle_id}"
        return await self._make_get_request(url, token)

    async def register_vehicle(self, vehicle_data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Register a new vehicle."""
        url = self.vehicle_url.strip().rstrip('/')
        if not url.endswith("/vehicles"):
            url = f"{url}/vehicles"
        return await self._make_post_request(url, token, vehicle_data)

    # 3. Projects
    async def request_modification_project(self, project_data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Request a new custom modification project."""
        url = f"{self.project_url}/projects"
        return await self._make_post_request(url, token, project_data)

    async def get_customer_projects(self, token: str) -> List[Dict[str, Any]]:
        """Get all projects for the current user."""
        url = f"{self.project_url}/projects"
        result = await self._make_get_request(url, token)
        # API returns ApiResponse with 'data' field
        if isinstance(result, dict) and 'data' in result and isinstance(result['data'], list):
            return result['data']
        return []

    async def get_project_details(self, project_id: str, token: str) -> Dict[str, Any]:
        """Get details for a specific project."""
        url = f"{self.project_url}/projects/{project_id}"
        result = await self._make_get_request(url, token)
        if isinstance(result, dict) and 'data' in result:
            return result['data']
        return result

    # 4. Profile
    async def get_my_profile(self, token: str) -> Dict[str, Any]:
        """Get current user profile."""
        base_url = self.auth_url.strip().rstrip('/')
        if base_url.endswith('/users'):
            url = f"{base_url}/me"
        else:
            url = f"{base_url}/users/me"
        return await self._make_get_request(url, token)

    async def update_my_profile(self, profile_data: Dict[str, Any], token: str) -> Dict[str, Any]:
        """Update current user profile."""
        base_url = self.auth_url.strip().rstrip('/')
        if base_url.endswith('/users'):
            url = f"{base_url}/profile"
        else:
            url = f"{base_url}/users/profile"
        return await self._make_put_request(url, token, profile_data)


# Singleton instance
_microservice_client_instance = None
def get_microservice_client() -> MicroserviceClient:
    global _microservice_client_instance
    if _microservice_client_instance is None:
        _microservice_client_instance = MicroserviceClient()
    return _microservice_client_instance