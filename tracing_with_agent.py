from tracing_manager import PhoenixTracingManager
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import FunctionTool
from llama_index.llms.ollama import Ollama

# 1. Initialize Tracing (You can call this safely in multiple agent files)
PhoenixTracingManager.enable_tracing(project_name="math-agent")

# 2. Define your tool
def multiply_numbers(a: int, b: int) -> int:
    """Multiplies two integers and returns the result."""
    return a * b

multiply_tool = FunctionTool.from_defaults(fn=multiply_numbers)

# 3. Initialize the LLM and the Agent
llm = Ollama(model="llama3", request_timeout=120.0)

agent = ReActAgent.from_tools(
    [multiply_tool], 
    llm=llm, 
    verbose=True
)

# 4. Execute a prompt
print("\nRunning agent query...")
response = agent.chat("What is 124 multiplied by 8?")
print(f"\nFinal Response: {response}")

input("\nPress Enter to exit...")
