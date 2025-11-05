# Agent_Bot/tools.py
from langchain.tools import tool
from .service_clients import client_check_availability, client_get_active_services, client_get_time_logs
from typing import List, Dict, Any
import json

# This token variable will be passed to the tools at runtime via AgentExecutor context
runtime_token = "" 

@tool
def check_appointment_slots_tool(date: str, service_type: str) -> str:
    """
    Checks the available appointment slots for a given date (YYYY-MM-DD) 
    and a defined service_type (e.g., 'Oil Change', 'Mod Installation') by calling the Appointment Service.
    Use this tool ONLY when the user asks for available times or scheduling.
    """
    result = client_check_availability(date, service_type, runtime_token)
    if result.get("error"):
        return f"Error: Could not check slots due to service error: {result['error']}"
    
    # Assuming result is a list of slot objects from the Appointment Service
    if result and isinstance(result, list):
        slots = [s['startTime'] for s in result if 'startTime' in s]
        if slots:
            return f"Available slots on {date} for {service_type}: {', '.join(slots)}. Please ask to book a specific slot."
    
    return f"No available slots found on {date} for {service_type}."

@tool
def get_user_active_services_tool() -> str:
    """
    Retrieves a list of all IN_PROGRESS services and projects for the current user. 
    Use this tool when the user asks for the status of their vehicle or project.
    """
    active_items = client_get_active_services(runtime_token)
    
    if not active_items:
        return "The user currently has no active services or modification projects."
    
    summary = "The user has the following items IN_PROGRESS:\n"
    for item in active_items:
        summary += f"- {item['type'].capitalize()} ID: {item['id']} (Status: {item['status']})\n"
        
    return summary.strip()

@tool
def get_last_work_log_tool(service_id: str) -> str:
    """
    Retrieves the most recent time log and technician note for a specific service or project ID.
    Use this when the user asks for detailed progress or what was done last.
    """
    logs = client_get_time_logs(service_id, runtime_token)
    if logs and isinstance(logs, list):
        # Time logs often return newest first, but we will sort to be safe
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