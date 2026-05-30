import os
import yaml
from pathlib import Path
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner
from llama_index.llms.ollama import Ollama
from llama_index.core.memory import SimpleChatStore  # Modern memory backing
# Assuming custom modern memory class implementation in your monorepo
from your_monorepo.memory import ModernMemoryContext 
from your_monorepo.mcp import BasicMcpClient

class SubagentFactory:
    def __init__(self, blueprints_dir: str):
        self.blueprints_dir = Path(blueprints_dir)
        self.chat_store = SimpleChatStore()

    async def create_agent(self, agent_id: str) -> AgentRunner:
        """Parses the MD file and returns an instantiated AgentRunner."""
        file_path = self.blueprints_dir / f"{agent_id}.md"
        if not file_path.exists():
            raise FileNotFoundError(f"Blueprint {agent_id}.md not found.")

        # Parse Frontmatter and Body
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split frontmatter from markdown body
        parts = content.split("---")
        if len(parts) < 3:
            raise ValueError("Invalid blueprint format. Expected YAML frontmatter.")
            
        config = yaml.safe_load(parts[1])
        system_prompt = parts[2].strip()

        # Initialize LLM via Ollama
        llm = Ollama(
            model=config.get("model", "llama3"), 
            temperature=config.get("temperature", 0.0),
            request_timeout=120.0
        )

        # Setup MCP Clients & Tools
        tools = []
        for mcp_conf in config.get("mcp_servers", []):
            mcp_client = BasicMcpClient(
                name=mcp_conf["name"],
                command=mcp_conf["command"],
                args=mcp_conf["args"]
            )
            await mcp_client.initialize()
            tools.extend(mcp_client.get_tools()) # Add retrieved tools

        # Initialize Modern Memory 
        memory = ModernMemoryContext(
            chat_store=self.chat_store, 
            chat_store_key=agent_id
        )

        # Assemble the Worker and Runner
        worker = FunctionCallingAgentWorker.from_tools(
            tools=tools,
            llm=llm,
            system_prompt=system_prompt,
        )
        
        return AgentRunner(agent_worker=worker, memory=memory)
