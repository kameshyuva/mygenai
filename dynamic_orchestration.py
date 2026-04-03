import json
import requests
from typing import List, Dict, Any
from llama_index.core.agent import FunctionAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama

# ==========================================
# 1. Define API Integration Tools (MCP Proxies)
# ==========================================
# In a real MCP setup, these functions live on the MCP server and make the actual HTTP requests.
# The docstrings provide the semantic glue that allows the LLM to route them dynamically.

# Mocking the base URL of your existing application
API_BASE_URL = "https://api.yourexistingapp.internal/v1"
API_HEADERS = {"Authorization": "Bearer internal-service-token-123"}

def get_user_ids_by_status(account_status: str) -> List[str]:
    """
    Queries the external application API to find users with a specific account status.
    Args:
        account_status (str): The status to filter by (e.g., 'active', 'churned', 'trial').
    Returns ONLY a list of string user IDs.
    """
    print(f"\n[API Execution] GET /users?status={account_status}")
    
    # --- Real Implementation Example ---
    # response = requests.get(
    #     f"{API_BASE_URL}/users", 
    #     params={"status": account_status}, 
    #     headers=API_HEADERS
    # )
    # response.raise_for_status()
    # return [user["id"] for user in response.json().get("data", [])]
    
    # --- Mocked Response for this example ---
    return ["usr_abc123", "usr_xyz789"]

def get_usage_metrics(user_ids: List[str]) -> str:
    """
    Fetches detailed API usage metrics from the external application for specific users.
    WARNING: You MUST provide a list of valid string user_ids to use this tool. 
    Do not guess IDs; fetch them using other tools first.
    """
    print(f"\n[API Execution] POST /metrics/usage with payload: {user_ids}")
    
    if not user_ids:
        return "Error: No user IDs provided."

    # --- Real Implementation Example ---
    # response = requests.post(
    #     f"{API_BASE_URL}/metrics/usage", 
    #     json={"user_ids": user_ids}, 
    #     headers=API_HEADERS
    # )
    # response.raise_for_status()
    # return json.dumps(response.json())
    
    # --- Mocked Response for this example ---
    mock_metrics = {
        "usr_abc123": {"total_requests": 45000, "rate_limited_count": 12},
        "usr_xyz789": {"total_requests": 150, "rate_limited_count": 0}
    }
    return json.dumps(mock_metrics)

# ==========================================
# 2. Wrap Tools and Configure Agent
# ==========================================
# Dynamically load the API wrapper tools
api_tools = [
    FunctionTool.from_defaults(fn=get_user_ids_by_status),
    FunctionTool.from_defaults(fn=get_usage_metrics)
]

llm = Ollama(model="llama3.1", request_timeout=120.0)

system_prompt = """
You are an integration agent connected to our core application via API tools.
Your goal is to fulfill user requests by combining data from these APIs.
Think step-by-step: if you need detailed metrics, ensure you first look up the exact user IDs required by the metrics tool.
Provide a clear, synthesized final answer based on the API responses.
"""

agent = FunctionAgent.from_tools(
    tools=api_tools,
    llm=llm,
    system_prompt=system_prompt
)

# ==========================================
# 3. Execution (Standard REST Response)
# ==========================================
print("--- Starting API Orchestration Workflow ---")

# The agent infers it must call `get_user_ids_by_status('active')` first,
# capture the array of string IDs, and pass them to `get_usage_metrics`.
response = agent.chat("Check our application APIs and tell me the usage metrics for our 'active' accounts. Are any of them hitting rate limits?")

print("\n--- Final Application Output ---")
print(response)
