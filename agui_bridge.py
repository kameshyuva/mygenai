from contextvars import ContextVar
from fastapi import APIRouter
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router

# Define the ContextVars at the module level
username_var: ContextVar[str] = ContextVar("username", default=None)
realm_var: ContextVar[str] = ContextVar("realm", default=None)
app_token_var: ContextVar[str] = ContextVar("app_token", default=None)

class AGUIBridgeRouter:
    def __init__(self, core_agent, router_model: str = "llama3"):
        self.core_agent = core_agent
        self.router_model = router_model
        self.router = self._build_router()

    def _delegate_to_core_agent(self, user_query: str) -> str:
        """Internal bridge function that executes the core agent."""
        
        # 1. Retrieve the specific headers for this request
        username = username_var.get()
        realm = realm_var.get()
        app_token = app_token_var.get()
        
        # 2. Inject the context into your core agent
        print(f"Executing for User: {username} | Realm: {realm} | Token: {app_token}")
        
        # You can now pass these to your core FunctionAgent if it accepts kwargs,
        # or use them to configure your SQLite vector store tenant filtering before calling chat()
        response = self.core_agent.chat(user_query)
        
        return str(response)

    def _build_router(self) -> APIRouter:
        core_agent_tool = FunctionTool.from_defaults(
            fn=self._delegate_to_core_agent,
            name="delegate_to_core_agent",
            description="Use this tool for ALL user queries to get the answer."
        )

        router_llm = Ollama(model=self.router_model, request_timeout=120.0) 
        system_prompt = "Pass exact user input to delegate_to_core_agent tool. Return exact output."

        return get_ag_ui_workflow_router(
            llm=router_llm,
            frontend_tools=[], 
            backend_tools=[core_agent_tool], 
            system_prompt=system_prompt,
            initial_state=None,
        )
