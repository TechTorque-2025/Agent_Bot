# services/appointment.py
import httpx
from datetime import datetime, timedelta
from config.settings import settings
import asyncio
import time
from typing import Dict, Any

class AppointmentService:
    def __init__(self):
        self.base_url = settings.APPOINTMENT_SERVICE_URL

    async def get_available_slots(self, date: str = None, token: str = None) -> dict:
        """
        Fetch available appointment slots from Appointment Service (ASYNC)
        Used by the RAG system's GeminiService (Friend's part)
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # Your API design uses /api/v1/appointments/availability
        url = f"{self.base_url}/availability" 
        params = {"date": date}

        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params, headers=headers)
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"available_slots": [], "message": "Unable to fetch slots at this time"}
        except Exception as e:
            return {"available_slots": [], "error": str(e), "business_hours": "Monday-Friday 8:00 AM - 6:00 PM"}

    def get_available_slots_sync(self, date: str = None, token: str = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for Agent Tools (blocks for result)
        Used by agent_tools.py
        """
        # A simple way to run an async function synchronously
        return asyncio.run(self.get_available_slots(date=date, token=token))

# Singleton instance
_appointment_service_instance = None
def get_appointment_service() -> AppointmentService:
    global _appointment_service_instance
    if _appointment_service_instance is None:
        _appointment_service_instance = AppointmentService()
    return _appointment_service_instance