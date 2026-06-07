# agent.py
from llama_index.core.agent import FunctionAgent
from mcpmanager import MultiTenantMCPManager, current_user_realm, current_user_token

# Configure the manager instance globally
# This instance will be referenced by FastAPI and the invocation layer
mcp_manager = MultiTenantMCPManager("http://localhost:8000/sse")

# System Prompt explicitly engineered for low-parameter local models (Llama 8b / Qwen 4b)
SYSTEM_PROMPT = """You are an Operations Analytics Agent assessing correlation events.
Your goal is to inspect tracking data loops and determine cause alerts.

### EXECUTION BOUNDS
1. DATA MATCHING: Take specific keys from tool outputs and pass them cleanly to following dependency steps.
2. REPETITION SAFETY: Never evaluate a specific tool with identical keys twice. If results do not change, STOP.
3. CONCISENESS: Output your final reasoning clearly based only on the returned Markdown tabular data grids.
"""

async def agent_invoke(query: str, realm: str, token: str, llm_instance) -> str:
    """
    Main invocation function called directly by FastAPI endpoint routes.
    """
    # 1. Bind headers directly to the ContextVars for this isolated asynchronous chain
    token_context_ref = current_user_token.set(token)
    realm_context_ref = current_user_realm.set(realm)
    
    try:
        # 2. Pull the global, pre-computed tool schema retriever pointer
        tool_retriever = mcp_manager.get_retriever()
        
        # 3. Assemble the function agent instance
        agent = FunctionAgent(
            tool_retriever=tool_retriever,
            llm=llm_instance,
            system_prompt=SYSTEM_PROMPT,
            max_steps=5, # Strict ceiling prevents local loops from draining CPU threads
            verbose=True
        )
        
        # 4. Trigger the computation loop
        response = await agent.achat(query)
        return str(response)
        
    finally:
        # 5. Clean up tracking references to clean memory states completely
        current_user_token.reset(token_context_ref)
        current_user_realm.reset(realm_context_ref)
