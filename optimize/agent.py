import asyncio
from llama_index.llms.ollama import Ollama
from llama_index.core.agent import FunctionAgent
from llama_index.core.memory import ChatMemoryBuffer # Modern namespace
from llama_index.core.tools.mcp import MCPToolSpec

async def main():
    # 1. CPU-OPTIMIZED LLM
    # num_thread: Matches your 8 cores
    # num_batch: 512 is the sweet spot for CPU cache efficiency
    llm = Ollama(
        model="llama3.1:8b-instruct-q4_K_M", 
        request_timeout=300.0,
        additional_kwargs={
            "num_thread": 8,
            "num_batch": 512,
            "temperature": 0 
        }
    )

    # 2. MCP TOOLS
    mcp_spec = MCPToolSpec(server_url="http://localhost:8000")
    tools = mcp_spec.to_tool_list()

    # 3. MODERN MEMORY
    # ChatMemoryBuffer acts as a sliding window. 
    # 3500 tokens allows for ~2.5 batches of alert tables to remain in 'sight'.
    memory = ChatMemoryBuffer.from_defaults(token_limit=3500)

    # 4. FUNCTION AGENT
    agent = FunctionAgent.from_tools(
        tools=tools,
        llm=llm,
        memory=memory,
        system_prompt=(
            "You are a Business Alert Analyst. Your task is to assess, cause-analyze, "
            "and rank alerts. \n"
            "PROCESS:\n"
            "1. Use 'fetch_alerts' with offset 0.\n"
            "2. Identify 'High' and 'Critical' severity alerts.\n"
            "3. Cross-reference 'cause' and 'impact' to validate 'rank'.\n"
            "4. If 'next_offset' is provided, fetch the next batch.\n"
            "5. After assessing all batches, provide a final ranked summary of the "
            "top 3 scenarios and recommended actions."
        )
    )

    # 5. EXECUTION
    query = "Analyze all alerts, rank them, and summarize the causes for the top 3."
    response = await agent.astream_chat(query)
    
    async for delta in response.response_gen:
        print(delta, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
