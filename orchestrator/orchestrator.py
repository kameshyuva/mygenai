from llama_index.core.tools import FunctionTool
from llama_index.core.agent import AgentRunner, FunctionCallingAgentWorker

class Orchestrator:
    def __init__(self, factory: SubagentFactory):
        self.factory = factory
        self.active_subagents = {}

    async def discover_agents(self) -> str:
        """Reads the blueprint directory and returns available agents."""
        agents = []
        for file in self.factory.blueprints_dir.glob("*.md"):
            agents.append(file.stem)
        return f"Available subagents: {', '.join(agents)}"

    async def dispatch_to_subagent(self, agent_id: str, query: str) -> str:
        """Instantiates (or reuses) a subagent and routes a query to it."""
        if agent_id not in self.active_subagents:
            # Instantiate dynamically via the template factory
            self.active_subagents[agent_id] = await self.factory.create_agent(agent_id)
        
        agent = self.active_subagents[agent_id]
        
        # Execute the run async to prevent blocking
        response = await agent.arun(query)
        return str(response)

    def build_orchestrator_agent(self, llm) -> AgentRunner:
        """Builds the main orchestrator."""
        discovery_tool = FunctionTool.from_defaults(fn=self.discover_agents)
        dispatch_tool = FunctionTool.from_defaults(fn=self.dispatch_to_subagent)
        
        worker = FunctionCallingAgentWorker.from_tools(
            tools=[discovery_tool, dispatch_tool],
            llm=llm,
            system_prompt="You are the lead orchestrator. Discover available subagents, and route specialized tasks to them. Synthesize their responses."
        )
        return AgentRunner(agent_worker=worker)
