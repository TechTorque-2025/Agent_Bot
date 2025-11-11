from langchain.tools import tool
from typing import Dict, Any, List
from .microservice_client import get_microservice_client # FIX: Imported getter function
import json

# Global variable to hold the token for the duration of the agent's run
runtime_token = "" 

# FIX: Get the singleton client instance immediately for use in tools
client = get_microservice_client() 

@tool
async def check_appointment_slots_tool(date: str, service_type: str) -> str:
    """
    Checks the available appointment slots for a given date (YYYY-MM-DD) 
    and service_type (e.g., 'Oil Change', 'Diagnostics'). 
    Use this tool ONLY when the user asks for available times or scheduling.
    """
    # FIX: Uses the ASYNC method on the client instance with the runtime_token
    result = await client.get_appointment_slots(date, service_type, runtime_token)
    
    if result.get("error"):
        return f"Error: Could not check slots due to service error: {result['error']}"
    
    slots = result.get("available_slots", [])
    
    if slots and isinstance(slots, list):
        slot_times = [s['time'] for s in slots if 'time' in s]
        if slot_times:
            return f"Available slots on {date} for {service_type}: {', '.join(slot_times)}. Ask the user to specify a time if they want to book."
    
    return f"No available slots found on {date} for {service_type}."

@tool
async def get_user_active_services_tool() -> str:
    """
    Retrieves a list of all IN_PROGRESS services and projects for the current user. 
    Use this tool when the user asks for the status of their vehicle or project.
    """
    # FIX: Uses the ASYNC method on the client instance with the runtime_token
    active_items = await client.get_active_services(runtime_token)
    
    if not active_items:
        return "The user currently has no active services or modification projects."
    
    summary = "The user has the following items IN_PROGRESS:\n"
    for item in active_items:
        summary += f"- {item['type'].capitalize()} ID: {item['id']} (Status: {item['status']})\n"
        
    return summary.strip()

@tool
async def get_last_work_log_tool(service_id: str) -> str:
    """
    Retrieves the most recent time log and technician note for a specific service or project ID.
    The service_id must be provided by the user or extracted from the conversation history.
    """
    # FIX: Uses the ASYNC method on the client instance with the runtime_token
    logs = await client.get_time_logs_for_service(service_id, runtime_token)

    if logs and isinstance(logs, list):
        # Sort by creation timestamp (assuming 'createdAt' is the key)
        logs.sort(key=lambda x: x.get('createdAt', ''), reverse=True) 
        most_recent_log = logs[0]
        
        return json.dumps({
            "date": most_recent_log.get('date'),
            "hours": most_recent_log.get('hours'),
            "description": most_recent_log.get('description', 'No note provided.'),
        })
        
    return f"No time logs found for service/project ID: {service_id}."

all_tools = [
    check_appointment_slots_tool,
    get_user_active_services_tool,
    get_last_work_log_tool
]