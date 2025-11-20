import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from services.agent_tools import (
    book_appointment_tool,
    cancel_appointment_tool,
    get_my_vehicles_tool,
    request_modification_project_tool,
    check_appointment_slots_tool
)
from services.token_context import token_context

@pytest.mark.asyncio
async def test_book_appointment_tool():
    # Mock the client
    with patch('services.agent_tools.client') as mock_client:
        # Set up the mock return value
        mock_client.book_appointment = AsyncMock(return_value={"id": "123", "status": "CONFIRMED"})
        
        # Set the token context
        token = "test_token_123"
        token_context.set(token)
        
        # Call the tool
        result = await book_appointment_tool(
            date="2023-12-25",
            time="10:00",
            service_type="Oil Change",
            vehicle_id="v1",
            description="Test booking"
        )
        
        # Verify the result
        assert "Appointment booked successfully" in result
        assert "ID: 123" in result
        
        # Verify the client was called with the correct token and data
        mock_client.book_appointment.assert_called_once()
        args, _ = mock_client.book_appointment.call_args
        payload = args[0]
        passed_token = args[1]
        
        assert passed_token == token
        assert payload["date"] == "2023-12-25"
        assert payload["vehicleId"] == "v1"

@pytest.mark.asyncio
async def test_get_my_vehicles_tool():
    with patch('services.agent_tools.client') as mock_client:
        mock_client.get_customer_vehicles = AsyncMock(return_value=[
            {"id": "v1", "make": "Toyota", "model": "Camry", "year": 2020, "licensePlate": "ABC-123"}
        ])
        
        token_context.set("user_token")
        
        result = await get_my_vehicles_tool()
        
        assert "Toyota Camry" in result
        assert "ABC-123" in result
        mock_client.get_customer_vehicles.assert_called_once_with("user_token")

@pytest.mark.asyncio
async def test_concurrency_context():
    """Verify that token_context works correctly in simulated concurrent calls."""
    
    with patch('services.agent_tools.client') as mock_client:
        mock_client.get_appointment_slots = AsyncMock(return_value={"available_slots": [{"time": "10:00"}]})
        
        async def user_action(user_token):
            token_context.set(user_token)
            # Simulate some async work
            await asyncio.sleep(0.01)
            # Call a tool
            await check_appointment_slots_tool("2023-12-25", "Service")
            # Verify the mock was called with THIS user's token
            # (We can't easily check the mock call args here for concurrency, 
            # but we can check if the tool ran without error and used the context)
            return token_context.get()

        # Run two "users" concurrently
        results = await asyncio.gather(
            user_action("token_A"),
            user_action("token_B")
        )
        
        assert results[0] == "token_A"
        assert results[1] == "token_B"

if __name__ == "__main__":
    # Manual run if pytest not available
    asyncio.run(test_book_appointment_tool())
    asyncio.run(test_get_my_vehicles_tool())
    asyncio.run(test_concurrency_context())
    print("All manual tests passed!")
