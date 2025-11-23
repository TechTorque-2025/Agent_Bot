import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock

# Some CI/test environments do not have langchain and google packages installed.
# Patch sys.modules with lightweight mocks so the module imports successfully and
# tests can instantiate AIAgentService via object.__new__ (skipping __init__).
import types

# Add module stubs so the service module imports succeed in test environments
if 'langchain' not in sys.modules:
    langchain_mod = types.ModuleType('langchain')
    sys.modules['langchain'] = langchain_mod

if 'langchain.tools' not in sys.modules:
    sys.modules['langchain.tools'] = types.ModuleType('langchain.tools')

if 'langchain.agents' not in sys.modules:
    sys.modules['langchain.agents'] = types.ModuleType('langchain.agents')

if 'langchain_core.prompts' not in sys.modules:
    sys.modules['langchain_core.prompts'] = types.ModuleType('langchain_core.prompts')

if 'langchain_google_genai' not in sys.modules:
    sys.modules['langchain_google_genai'] = types.ModuleType('langchain_google_genai')

# Populate required names so imports succeed
langchain_agents = sys.modules.get('langchain.agents')
setattr(langchain_agents, 'AgentExecutor', type('AgentExecutor', (), {}))
setattr(langchain_agents, 'initialize_agent', lambda *a, **k: MagicMock())
setattr(langchain_agents, 'AgentType', type('AgentType', (), {}))

langchain_tools = sys.modules.get('langchain.tools')
class _StructuredTool:
    @classmethod
    def from_function(cls, *args, **kwargs):
        return None
setattr(langchain_tools, 'StructuredTool', _StructuredTool)

langchain_prompts = sys.modules.get('langchain_core.prompts')
setattr(langchain_prompts, 'ChatPromptTemplate', type('ChatPromptTemplate', (), {'from_messages': classmethod(lambda cls, x: None)}))
setattr(langchain_prompts, 'MessagesPlaceholder', type('MessagesPlaceholder', (), {}))

setattr(sys.modules.get('langchain_google_genai'), 'ChatGoogleGenerativeAI', type('ChatGoogleGenerativeAI', (), {}))

# Import the class directly
from services.agent_core import AIAgentService


@pytest.mark.asyncio
async def test_invoke_agent_falls_back_to_sync_run():
    # Create an instance without running __init__ to avoid creating LLMs
    agent = object.__new__(AIAgentService)

    # Prepare a synchronous agent_executor (no `ainvoke`) whose run returns (output, intermediate_steps)
    class SyncExecutor:
        def run(self, payload):
            return ("sync output", [("action1", "tool-output")])

    agent.agent_executor = SyncExecutor()

    # Mock microservice client and rag service
    agent.ms_client = MagicMock()
    agent.ms_client.get_user_context = AsyncMock(return_value={"id": "user-x"})

    rag = MagicMock()
    rag.retrieve_and_format = MagicMock(return_value={"context": "kb", "num_sources": 0})
    agent.rag_service = rag

    # Call invoke_agent
    result = await agent.invoke_agent("hello", "s1", "tok", [])

    assert isinstance(result, dict)
    assert result.get("output") == "sync output"


@pytest.mark.asyncio
async def test_invoke_agent_uses_ainvoke_when_present():
    agent = object.__new__(AIAgentService)

    class AsyncExecutor:
        async def ainvoke(self, payload):
            return {"output": "async output", "intermediate_steps": []}

    agent.agent_executor = AsyncExecutor()
    agent.ms_client = MagicMock()
    agent.ms_client.get_user_context = AsyncMock(return_value={})

    rag = MagicMock()
    rag.retrieve_and_format = MagicMock(return_value={"context": "kb", "num_sources": 1})
    agent.rag_service = rag

    result = await agent.invoke_agent("ask me", "s2", "tok2", [])

    assert result.get("output") == "async output"
