# services/agent_core.py

from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from services.agent_tools import all_tools
from services.microservice_client import MicroserviceClient
from services.rag import get_rag_service
from services.token_context import token_context
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
            "You are 'TechTorque AI Assistant', a friendly and professional vehicle service chatbot for TechTorque Auto Services. "
            "Your mission is to help customers with their vehicle service needs in a warm, helpful manner.\n"
            "\n**YOUR CAPABILITIES:**\n"
            "- Answer questions about vehicle services, repairs, maintenance, and appointments\n"
            "- Help schedule and manage service appointments (Book, Cancel, Check Slots)\n"
            "- Manage user vehicles (List, Register, View Details)\n"
            "- Handle custom modification projects (Request, List, View Details)\n"
            "- Manage user profile (View, Update)\n"
            "- Check service status and work logs\n"
            "- Give automotive advice and recommendations\n"
            "\n**CRITICAL INSTRUCTION: CHAIN OF THOUGHT REASONING**\n"
            "Before taking action, you MUST think step-by-step. For example:\n"
            "- If user wants to book: 1. Check if they have a vehicle (`get_my_vehicles`). 2. If no vehicle, ask to register (`register_vehicle`). 3. If vehicle exists, check slots (`check_appointment_slots`). 4. Finally, book (`book_appointment`).\n"
            "- If user wants to request a project: 1. Check vehicle. 2. Request project (`request_modification_project`).\n"
            "\n**CONVERSATION STYLE:**\n"
            "- Be friendly, warm, patient, and professional\n"
            "- Use emojis to make conversations more engaging and user-friendly (👋 🚗 ✅ 🔧 ⏰ 💰 😊 👍 🎉 etc.)\n"
            "- Use clear, simple, conversational language\n"
            "- For greetings (hi/hello), respond warmly with: 'Hi there! 👋 How can I help you with your vehicle today? 🚗'\n"
            "- When users thank you, respond with: 'You're welcome! 😊 Let me know if you need anything else! 👍'\n"
            "- Use appropriate emojis for different contexts:\n"
            "  * Greetings: 👋 😊\n"
            "  * Cars/Vehicles: 🚗 🚙 🔧 🛠️\n"
            "  * Appointments: 📅 ⏰ ✅\n"
            "  * Pricing: 💰 💵\n"
            "  * Success: ✅ 🎉 👍\n"
            "  * Warning: ⚠️ ⚡\n"
            "  * Help: 💡 ℹ️\n"
            "\n**SCOPE BOUNDARIES:**\n"
            "- Stay focused on automotive and service-related topics\n"
            "- For completely unrelated topics (politics, entertainment, etc.), politely redirect: "
            "'I specialize in vehicle services. 🚗 How can I help you with your car today?'\n"
            "\n**TOOLS & KNOWLEDGE:**\n"
            "- Use the provided tools for real-time data (appointments, service status, work logs)\n"
            "- Use the Knowledge Base below for general information (hours, policies, service details)\n"
            "\n**Current User Context:** {user_context}\n"
            "**Knowledge Base:**\n{rag_context}"
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
            query_lower = user_query.lower().strip()

            # Allow common greetings and conversational starters
            greeting_keywords = [
                'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon',
                'good evening', 'help', 'thanks', 'thank you', 'bye', 'goodbye'
            ]

            # Check if it's a greeting (let it pass to the agent)
            is_greeting = any(greeting in query_lower for greeting in greeting_keywords)

            # Use a simple keyword check for automotive topics
            automotive_keywords = [
                'car', 'vehicle', 'auto', 'engine', 'tire', 'brake', 'oil', 'repair',
                'service', 'maintenance', 'appointment', 'mechanic', 'transmission',
                'battery', 'diagnostic', 'warranty', 'part', 'labor', 'wheel', 'suspension',
                'schedule', 'booking', 'status', 'price', 'cost', 'estimate'
            ]
            has_automotive_keyword = any(keyword in query_lower for keyword in automotive_keywords)

            # If no RAG results AND no automotive keywords AND not a greeting, it's likely off-topic
            if not has_automotive_keyword and not is_greeting:
                logger.info(f"Query appears off-topic (no RAG results, no automotive keywords): {user_query}")
                return {
                    "output": "I'm sorry, but I can only answer questions related to vehicle services and appointments. How can I help you with your car today?",
                    "tool_executed": None
                }
        
        # 3. CRITICAL: Inject Runtime Token into ContextVar
        # This ensures thread-safety for concurrent users
        token_context.set(user_token)
        
        # 4. Convert chat history to LangChain message objects
        # The MessagesPlaceholder expects HumanMessage and AIMessage objects, not plain dicts
        langchain_history = []
        for msg in chat_history:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            if role == "user" or role == "human":
                langchain_history.append(HumanMessage(content=content))
            elif role == "assistant" or role == "ai":
                langchain_history.append(AIMessage(content=content))
        
        # 5. Invoke Agent Executor (try async, fallback to sync if async is not available)
        raw_result = None
        try:
            # some AgentExecutor versions expose an async method named `ainvoke`
            if hasattr(self.agent_executor, "ainvoke"):
                raw_result = await self.agent_executor.ainvoke({
                    "input": user_query,
                    "chat_history": langchain_history,
                    "user_context": user_context_str, # Injected into System Prompt
                    "rag_context": rag_context_str    # Injected into System Prompt
                })
            else:
                # Fallback: call the synchronous `run` in a thread if async method missing
                logger.info("AgentExecutor does not expose `ainvoke`, using sync `run` in an executor as fallback")
                import asyncio as _asyncio
                raw_result = await _asyncio.to_thread(
                    self.agent_executor.run,
                    {
                        "input": user_query,
                        "chat_history": langchain_history,
                        "user_context": user_context_str,
                        "rag_context": rag_context_str
                    }
                )

        except Exception as ex:
            # Log exception with stack trace for easier debugging and re-raise
            logger.exception("AgentExecutor invocation failed")
            raise
        
        # 6. Determine Tool Execution Status
        tool_executed = None

        # Normalize raw_result into the expected structure
        intermediate_steps = []
        result = {}

        try:
            if isinstance(raw_result, dict):
                # When agent returns a dict-like response
                result = raw_result
                intermediate_steps = result.get('intermediate_steps', []) or []
            elif isinstance(raw_result, tuple) and len(raw_result) >= 2:
                # Common return shape when return_intermediate_steps=True -> (output, intermediate_steps)
                result = {"output": raw_result[0], "intermediate_steps": raw_result[1]}
                intermediate_steps = raw_result[1] or []
            elif isinstance(raw_result, str):
                # Simple string output
                result = {"output": raw_result}
            else:
                # Any other shape - convert to string for output
                result = {"output": str(raw_result)}
        except Exception:
            logger.exception("Failed to normalize agent executor output; converting to string")
            result = {"output": str(raw_result)}

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