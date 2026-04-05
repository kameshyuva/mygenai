# agui_bridge.py
from contextvars import ContextVar
from fastapi import APIRouter
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router

username_var: ContextVar[str] = ContextVar("username", default=None)
realm_var: ContextVar[str] = ContextVar("realm", default=None)
app_token_var: ContextVar[str] = ContextVar("app_token", default=None)

class AGUIBridgeRouter:
    def __init__(self, router_model: str = "llama3"):
        # Start as None. It will be injected during FastAPI startup.
        self.core_agent = None 
        self.router_model = router_model
        self.router = self._build_router()

    def set_core_agent(self, agent_instance):
        """Inject the fully built async agent into the bridge."""
        self.core_agent = agent_instance

    # Change to async def to support your async agent builder
    async def _delegate_to_core_agent(self, user_query: str) -> str:
        """Internal bridge function that executes the core agent."""
        if self.core_agent is None:
            raise RuntimeError("Core agent has not been initialized via lifespan.")

        username = username_var.get()
        realm = realm_var.get()
        app_token = app_token_var.get()
        
        print(f"Executing for User: {username} | Realm: {realm} | Token: {app_token}")
        
        # Use achat() to execute the agent asynchronously without blocking the event loop.
        # This will return a normal, non-streaming response.
        response = await self.core_agent.achat(user_query)
        
        return str(response)

    def _build_router(self) -> APIRouter:
        # Use async_fn instead of fn to register an asynchronous tool
        core_agent_tool = FunctionTool.from_defaults(
            async_fn=self._delegate_to_core_agent,
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
