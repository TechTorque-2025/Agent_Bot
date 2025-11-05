# Agent_Bot/agent_core.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .tools import all_tools, runtime_token 
from .models import UserContext
import os
from typing import List, Dict, Any

# 1. Initialize the LLM
llm = ChatGoogleGenerativeAI(
    model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), 
    temperature=0
)

# 2. Define the System Prompt
SYSTEM_PROMPT = (
    "You are 'TechTorque Assistant', a friendly, professional, and knowledgeable AI agent for a premium vehicle service shop. "
    "Your goal is to answer user questions, check service status, and book appointments using your tools. "
    "ALWAYS use the provided tools if the question relates to scheduling or status. "
    "Here is the user's context (vehicles and ID) which you can reference but should NOT show to the user unless needed for clarity: {user_context}"
)

# 3. Create the Agent Prompt Template
agent_prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# 4. Create the Agent Executor
agent = create_tool_calling_agent(llm, all_tools, agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=all_tools, verbose=True)

# 5. Function to run the agent from the FastAPI endpoint
def run_agent(query: str, chat_history: List[Dict[str, Any]], user_context: UserContext, token: str) -> str:
    """The main execution function called by the FastAPI controller."""
    
    # CRITICAL: Inject the user's token into the global variable that the tools use
    # This is a simple, effective pattern for stateful agent execution
    global runtime_token
    runtime_token = token
    
    # Format the user context for the prompt
    context_str = f"User ID: {user_context.user_id}, Name: {user_context.full_name}, Vehicles: {user_context.vehicles}"
    
    # The agent uses the formatted context in the system prompt
    result = agent_executor.invoke({
        "input": query,
        "chat_history": chat_history,
        "user_context": context_str
    })
    return result["output"]