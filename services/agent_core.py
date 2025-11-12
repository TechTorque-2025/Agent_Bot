# services/agent_core.py

from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from services.agent_tools import all_tools
from services.microservice_client import MicroserviceClient
from services.rag import get_rag_service
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# --- Singleton setup (similar to the friend's service pattern) ---
class AIAgentService:
    def __init__(self):
        # 1. LLM for Agent
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL, 
            temperature=0, 
            google_api_key=settings.GOOGLE_API_KEY
        )
        # 2. RAG Service for knowledge retrieval
        self.rag_service = get_rag_service()
        self.ms_client = MicroserviceClient()
        
        # 3. The Agent Prompt (Will be formatted at runtime)
        self.SYSTEM_PROMPT = (
            "You are 'TechTorque AI Assistant', a premium, professional vehicle service agent. "
            "Your persona is friendly, accurate, and focused ONLY on vehicle services, appointments, and company policies. "
            "\n\nIMPORTANT SCOPE RESTRICTIONS:\n"
            "- You can ONLY answer questions related to: vehicle services, repairs, appointments, warranty, company policies, and automotive topics.\n"
            "- You MUST refuse to answer questions about: general knowledge, history, geography, science, entertainment, politics, or any non-automotive topics.\n"
            "- If asked an off-topic question, respond: 'I'm sorry, but I can only answer questions related to vehicle services and appointments. How can I help you with your car today?'\n"
            "\n\nTOOL USAGE:\n"
            "- Use the provided tools for real-time data (appointments, user service status, work logs).\n"
            "- Use the 'Knowledge Base' below for general information (hours, policies, service descriptions).\n"
            "\nCurrent User Context (CRUCIAL): {user_context}\n"
            "Knowledge Base:\n{rag_context}"
        )
        
        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        """Assembles the LangChain Agent."""
        
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", self.SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Build an AgentExecutor using the project prompt and the available tools.
        # Use the deprecated initialize_agent helper which returns an AgentExecutor
        # and pass our chat prompt via agent_kwargs so the underlying agent uses it.
        # STRUCTURED_CHAT supports multi-input tools (needed for appointment checking)
        agent_executor = initialize_agent(
            all_tools,
            self.llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            agent_kwargs={"prompt": agent_prompt},
            verbose=True,
            handle_parsing_errors=True,
            # IMPORTANT: Return intermediate steps so we can detect tool usage
            return_intermediate_steps=True,
        )
        return agent_executor

    async def invoke_agent(
        self,
        user_query: str,
        session_id: str,
        user_token: str,
        chat_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Runs the agent with all retrieved context and history."""

        # 1. Retrieve User Context (My Original Logic)
        user_context_data = await self.ms_client.get_user_context(user_token)
        user_context_str = str(user_context_data)
        
        # 2. Retrieve RAG Context and check relevance
        rag_result = self.rag_service.retrieve_and_format(query=user_query)
        rag_context_str = rag_result.get("context", "Knowledge base temporarily unavailable.")

        # Pre-filter: If RAG returned no relevant documents, check if query is automotive-related
        if rag_result.get("num_sources", 0) == 0:
            # Use a simple keyword check for automotive topics
            automotive_keywords = [
                'car', 'vehicle', 'auto', 'engine', 'tire', 'brake', 'oil', 'repair',
                'service', 'maintenance', 'appointment', 'mechanic', 'transmission',
                'battery', 'diagnostic', 'warranty', 'part', 'labor', 'wheel', 'suspension'
            ]
            query_lower = user_query.lower()
            has_automotive_keyword = any(keyword in query_lower for keyword in automotive_keywords)

            # If no RAG results AND no automotive keywords, it's likely off-topic
            if not has_automotive_keyword:
                logger.info(f"Query appears off-topic (no RAG results, no automotive keywords): {user_query}")
                return {
                    "output": "I'm sorry, but I can only answer questions related to vehicle services and appointments. How can I help you with your car today?",
                    "tool_executed": None
                }
        
        # 3. CRITICAL: Inject Runtime Variables into Tools
        # This is needed because tools are defined globally but need runtime data
        for tool in all_tools:
            if hasattr(tool, 'runtime_token'):
                tool.runtime_token = user_token
        
        # 4. Invoke Agent Executor (use ainvoke for async tools)
        result = await self.agent_executor.ainvoke({
            "input": user_query,
            "chat_history": chat_history,
            "user_context": user_context_str, # Injected into System Prompt
            "rag_context": rag_context_str    # Injected into System Prompt
        })
        
        # 5. Determine Tool Execution Status
        tool_executed = None
        intermediate_steps = result.get('intermediate_steps', [])

        if intermediate_steps:
            # intermediate_steps is a list of tuples: (AgentAction, tool_output)
            for step in intermediate_steps:
                if isinstance(step, tuple) and len(step) >= 1:
                    agent_action = step[0]
                    if hasattr(agent_action, 'tool'):
                        tool_name = agent_action.tool
                        if 'appointment' in tool_name.lower():
                            tool_executed = "Appointment_Check"
                            break
                        elif 'active_services' in tool_name.lower():
                            tool_executed = "Active_Services_Check"
                            break
                        elif 'work_log' in tool_name.lower():
                            tool_executed = "Work_Log_Check"
                            break

        return {
            "output": result.get("output"),
            "tool_executed": tool_executed
        }

# Singleton Instance
_agent_service_instance = None
def get_agent_service() -> AIAgentService:
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AIAgentService()
    return _agent_service_instance