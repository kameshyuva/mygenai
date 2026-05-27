# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "llama-index-core",
#   "llama-index-llms-openai-like",
#   "arize-phoenix"
# ]
# ///

import asyncio
import phoenix as px
from llama_index.core import set_global_handler
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.agent import FunctionCallingAgentWorker, AgentRunner

# ---------------------------------------------------------
# 1. Initialize Observability
# ---------------------------------------------------------
px.launch_app()
set_global_handler("arize_phoenix")

# ---------------------------------------------------------
# 2. Define Tools
# ---------------------------------------------------------
def assess_business_alert(alert_id: str) -> str:
    """Finds the cause of a business alert and recommends an action."""
    # In a production environment, this would query a real monitoring API
    return f"Alert {alert_id} was caused by a CPU spike. Recommendation: scale up workers."

async def main():
    # ---------------------------------------------------------
    # 3. Configure the LLM with API-side Generation Parameters
    # ---------------------------------------------------------
    llm = OpenAILike(
        api_base="http://localhost:8080/v1",
        api_key="fake-key",
        model="local-model",
        is_chat_model=True,
        is_function_calling_model=True,
        timeout=120.0,
        additional_kwargs={
            "seed": 42,
            "extra_body": {
                "min_p": 0.05,
                "repeat_penalty": 1.15
            }
        }
    )

    # ---------------------------------------------------------
    # 4. Initialize the Async Agent
    # ---------------------------------------------------------
    alert_tool = FunctionTool.from_defaults(fn=assess_business_alert)
    
    worker = FunctionCallingAgentWorker.from_tools(
        tools=[alert_tool],
        llm=llm,
        verbose=True
    )
    
    agent = AgentRunner(worker)
    
    # ---------------------------------------------------------
    # 5. Execute
    # ---------------------------------------------------------
    print("Sending asynchronous request to the local agent...\n")
    response = await agent.achat("Can you assess the status and provide a recommendation for alert ID 9942?")
    
    print("\nFinal Response:")
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
