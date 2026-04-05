from fastapi import APIRouter
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama
from llama_index.protocols.ag_ui.router import get_ag_ui_workflow_router

class AGUIBridgeRouter:
    def __init__(self, core_agent, router_model: str = "llama3"):
        """
        Initializes the AG-UI protocol bridge.
        
        Args:
            core_agent: Your existing LlamaIndex FunctionAgent instance.
            router_model: The lightweight Ollama model used purely for routing.
        """
        self.core_agent = core_agent
        self.router_model = router_model
        
        # Build and expose the FastAPI router upon initialization
        self.router = self._build_router()

    def _delegate_to_core_agent(self, user_query: str) -> str:
        """Internal bridge function that executes the core agent."""
        # Executes the core agent normally (non-streaming)
        response = self.core_agent.chat(user_query)
        return str(response)

    def _build_router(self) -> APIRouter:
        """Constructs the AG-UI workflow router with the wrapped tool."""
        
        # 1. Convert the bridge method into a LlamaIndex Tool
        core_agent_tool = FunctionTool.from_defaults(
            fn=self._delegate_to_core_agent,
            name="delegate_to_core_agent",
            description="Use this tool for ALL user queries to get the answer."
        )

        # 2. Configure the lightweight router LLM
        router_llm = Ollama(model=self.router_model, request_timeout=120.0) 

        # 3. Token-Optimized System Prompt
        system_prompt = "Pass exact user input to delegate_to_core_agent tool. Return exact output."

        # 4. Generate and return the router
        return get_ag_ui_workflow_router(
            llm=router_llm,
            frontend_tools=[], 
            backend_tools=[core_agent_tool], 
            system_prompt=system_prompt,
            initial_state=None,
        )
