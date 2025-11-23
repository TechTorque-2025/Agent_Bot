from langchain.tools import StructuredTool
from typing import Dict, Any, List, Optional
from .microservice_client import get_microservice_client
from services.token_context import token_context
import json

# Attempt to get the singleton client instance - make import resilient (tests may not have httpx installed)
try:
    client = get_microservice_client()
except Exception as e:
    # Tests will patch `services.agent_tools.client` as needed; avoid hard failures during import
    import logging
    logging.getLogger(__name__).warning("Microservice client not available at import time: %s", e)
    client = None

# --- 1. Appointment Tools ---

async def check_appointment_slots_tool(date: str, service_type: str) -> str:
    """
    Checks available appointment slots.
    Use when user asks for available times.
    """
    token = token_context.get()
    result = await client.get_appointment_slots(date, service_type, token)
    
    if result.get("error"):
        return f"Error checking slots: {result['error']}"
    
    slots = result.get("available_slots", [])
    if slots and isinstance(slots, list):
        slot_times = [s['time'] for s in slots if 'time' in s]
        if slot_times:
            return f"Available slots on {date} for {service_type}: {', '.join(slot_times)}."

    return f"No available slots found on {date} for {service_type}."

async def book_appointment_tool(date: str, time: str, service_type: str, vehicle_id: str, description: str = "") -> str:
    """
    Books a new appointment.
    REQUIRED: date (YYYY-MM-DD), time (HH:mm), service_type, vehicle_id.
    """
    token = token_context.get()
    payload = {
        "date": date,
        "time": time,
        "serviceType": service_type,
        "vehicleId": vehicle_id,
        "description": description
    }
    result = await client.book_appointment(payload, token)
    
    if result.get("error"):
        return f"Failed to book appointment: {result['error']}"
    
    return f"Appointment booked successfully! ID: {result.get('id')}. Status: {result.get('status')}."

async def cancel_appointment_tool(appointment_id: str) -> str:
    """
    Cancels an existing appointment.
    REQUIRED: appointment_id.
    """
    token = token_context.get()
    result = await client.cancel_appointment(appointment_id, token)
    
    if result.get("error"):
        return f"Failed to cancel appointment: {result['error']}"
    
    return "Appointment cancelled successfully."

# --- 2. Vehicle Tools ---

async def get_my_vehicles_tool() -> str:
    """
    Lists all vehicles belonging to the current user.
    Use to find vehicle_id for booking.
    """
    token = token_context.get()
    vehicles = await client.get_customer_vehicles(token)
    
    if not vehicles:
        return "You have no registered vehicles."
    
    summary = "Your Vehicles:\n"
    for v in vehicles:
        # tolerate different JSON shapes from services (camelCase vs snake_case)
        make = v.get('make') or v.get('Make') or ''
        model = v.get('model') or v.get('Model') or ''
        year = v.get('year') or v.get('Year') or ''
        plate = v.get('licensePlate') or v.get('license_plate') or v.get('plate') or ''
        vid = v.get('vehicleId') or v.get('id') or v.get('vehicle_id') or ''

        summary += f"- {make} {model} ({year}) - Plate: {plate} - ID: {vid}\n"
    return summary

async def get_vehicle_details_tool(vehicle_id: str) -> str:
    """
    Get detailed info for a specific vehicle.
    """
    token = token_context.get()
    result = await client.get_vehicle_details(vehicle_id, token)
    
    if result.get("error"):
        return f"Error fetching vehicle details: {result['error']}"
    
    return json.dumps(result, indent=2)

async def register_vehicle_tool(make: str, model: str, year: int, license_plate: str, vin: str) -> str:
    """
    Registers a new vehicle.
    REQUIRED: make, model, year, license_plate, vin.
    """
    token = token_context.get()
    payload = {
        "make": make,
        "model": model,
        "year": year,
        "licensePlate": license_plate,
        "vin": vin
    }
    result = await client.register_vehicle(payload, token)
    
    if result.get("error"):
        return f"Failed to register vehicle: {result['error']}"
    
    return f"Vehicle registered successfully! ID: {result.get('vehicleId')}"

# --- 3. Project Tools ---

async def request_modification_project_tool(vehicle_id: str, description: str, budget: float, desired_completion_date: str) -> str:
    """
    Requests a new custom modification project.
    REQUIRED: vehicle_id, description, budget, desired_completion_date (YYYY-MM-DD).
    """
    token = token_context.get()
    payload = {
        "vehicleId": vehicle_id,
        "description": description,
        "budget": budget,
        "desiredCompletionDate": desired_completion_date,
        "projectType": "MODIFICATION"
    }
    result = await client.request_modification_project(payload, token)
    
    if result.get("error"):
        return f"Failed to request project: {result['error']}"
    
    data = result.get('data', {})
    return f"Project requested successfully! ID: {data.get('id')}. Status: {data.get('status')}."

async def get_my_projects_tool() -> str:
    """
    Lists all custom projects for the user.
    """
    token = token_context.get()
    projects = await client.get_customer_projects(token)
    
    if not projects:
        return "You have no active projects."
    
    summary = "Your Projects:\n"
    for p in projects:
        summary += f"- Project ID: {p.get('id')} - Status: {p.get('status')} - {p.get('description')[:50]}...\n"
    return summary

async def get_project_details_tool(project_id: str) -> str:
    """
    Get details for a specific project.
    """
    token = token_context.get()
    result = await client.get_project_details(project_id, token)
    
    if result.get("error"):
        return f"Error fetching project details: {result['error']}"
    
    return json.dumps(result, indent=2)

# --- 4. Profile Tools ---

async def get_my_profile_tool() -> str:
    """
    Get current user profile details.
    """
    token = token_context.get()
    result = await client.get_my_profile(token)
    
    if result.get("error"):
        return f"Error fetching profile: {result['error']}"
    
    return json.dumps(result, indent=2)

async def update_my_profile_tool(full_name: str = None, phone: str = None, address: str = None) -> str:
    """
    Update user profile.
    Only provide fields that need updating.
    """
    token = token_context.get()
    payload = {}
    if full_name: payload['fullName'] = full_name
    if phone: payload['phone'] = phone
    if address: payload['address'] = address
    
    if not payload:
        return "No changes provided."
        
    result = await client.update_my_profile(payload, token)
    
    if result.get("error"):
        return f"Failed to update profile: {result['error']}"
    
    return "Profile updated successfully."

# --- 5. Existing Tools (Updated) ---

async def get_user_active_services_tool() -> str:
    """
    Retrieves IN_PROGRESS services/projects.
    """
    token = token_context.get()
    active_items = await client.get_active_services(token)
    
    if not active_items:
        return "No active services or projects."
    
    summary = "Active Items:\n"
    for item in active_items:
        summary += f"- {item['type'].capitalize()} ID: {item['id']} (Status: {item['status']})\n"
    return summary

async def get_last_work_log_tool(service_id: str) -> str:
    """
    Retrieves recent work logs for a service/project.
    """
    token = token_context.get()
    logs = await client.get_time_logs_for_service(service_id, token)

    if logs and isinstance(logs, list):
        logs.sort(key=lambda x: x.get('createdAt', ''), reverse=True) 
        most_recent_log = logs[0]
        return json.dumps({
            "date": most_recent_log.get('date'),
            "hours": most_recent_log.get('hours'),
            "description": most_recent_log.get('description', 'No note provided.'),
        })

    return f"No logs found for ID: {service_id}."

# --- Tool Definitions ---

all_tools = [
    # Appointments
    StructuredTool.from_function(coroutine=check_appointment_slots_tool, name="check_appointment_slots", description="Check available slots. Args: date (YYYY-MM-DD), service_type"),
    StructuredTool.from_function(coroutine=book_appointment_tool, name="book_appointment", description="Book appointment. Args: date, time, service_type, vehicle_id, description"),
    StructuredTool.from_function(coroutine=cancel_appointment_tool, name="cancel_appointment", description="Cancel appointment. Args: appointment_id"),
    
    # Vehicles
    StructuredTool.from_function(coroutine=get_my_vehicles_tool, name="get_my_vehicles", description="List user vehicles. Returns IDs needed for booking."),
    StructuredTool.from_function(coroutine=get_vehicle_details_tool, name="get_vehicle_details", description="Get vehicle details. Args: vehicle_id"),
    StructuredTool.from_function(coroutine=register_vehicle_tool, name="register_vehicle", description="Register new vehicle. Args: make, model, year, license_plate, vin"),
    
    # Projects
    StructuredTool.from_function(coroutine=request_modification_project_tool, name="request_modification_project", description="Request custom project. Args: vehicle_id, description, budget, desired_completion_date"),
    StructuredTool.from_function(coroutine=get_my_projects_tool, name="get_my_projects", description="List user projects."),
    StructuredTool.from_function(coroutine=get_project_details_tool, name="get_project_details", description="Get project details. Args: project_id"),
    
    # Profile
    StructuredTool.from_function(coroutine=get_my_profile_tool, name="get_my_profile", description="Get user profile info."),
    StructuredTool.from_function(coroutine=update_my_profile_tool, name="update_my_profile", description="Update profile. Args: full_name, phone, address"),
    
    # Existing / Status
    StructuredTool.from_function(coroutine=get_user_active_services_tool, name="get_active_services", description="Check active services/projects status."),
    StructuredTool.from_function(coroutine=get_last_work_log_tool, name="get_work_logs", description="Get work logs for service_id.")
]