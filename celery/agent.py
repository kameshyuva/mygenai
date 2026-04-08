from llama_index.llms.ollama import Ollama
from llama_index.tools.mcp import MCPServerClient
from llama_index.core.agent.workflow import (
    FunctionAgent, 
    AgentStream, 
    ToolCall, 
    ToolCallResult
)
from llama_index.core.memory import ChatMemoryBuffer

class MCPStreamingAgent:
    def __init__(self, mcp_url: str = "http://localhost:8000", model: str = "llama3.1"):
        # 1. Initialize LLM
        self.llm = Ollama(model=model, request_timeout=120.0)
        
        # 2. Initialize MCP Tools
        self.mcp_client = MCPServerClient(url=mcp_url)
        self.tools = self.mcp_client.get_tools()
        
        # 3. Initialize Memory
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=8000)
        
        # 4. Initialize FunctionAgent
        self.agent = FunctionAgent(
            tools=self.tools,
            llm=self.llm,
            memory=self.memory,
            system_prompt="You are a helpful assistant. Use tools when necessary."
        )

    async def stream_run(self, prompt: str):
        """
        Executes the agent and yields agnostic, dictionary-based events.
        Does NOT know about Redis or Celery.
        """
        handler = self.agent.run(user_msg=prompt)
        
        try:
            async for event in handler.stream_events():
                if isinstance(event, AgentStream):
                    yield {"type": "stream", "content": event.delta}
                    
                elif isinstance(event, ToolCall):
                    yield {"type": "tool_call", "tool": event.tool_name, "kwargs": event.tool_kwargs}
                    
                elif isinstance(event, ToolCallResult):
                    yield {"type": "tool_result", "tool": event.tool_name, "result": str(event.tool_result)}
                    
            # Wait for final resolution
            await handler
            yield {"type": "done"}
            
        except Exception as e:
            yield {"type": "error", "content": str(e)}
            raise e
