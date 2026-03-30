# agent.py
import asyncio
import time
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel, Field, ValidationError

from llama_index.llms.openai import OpenAI
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.core.tools import FunctionTool
from llama_index.core.agent.workflow import FunctionAgent

# --- 1. Define the Generic Envelope ---
T = TypeVar("T")

class StandardAPIResponse(BaseModel, Generic[T]):
    status: str = Field(default="success", description="'success', 'fail', or 'error'")
    message: Optional[str] = Field(default=None)
    data: Optional[T] = Field(default=None)
    metadata: Optional[dict] = Field(default_factory=dict)
    errors: Optional[Any] = Field(default=None)

# --- 2. Define the Structured Output Schema ---
class DatabaseSummary(BaseModel):
    tables_analyzed: list[str] = Field(..., description="List of tables the agent found and queried")
    key_findings: str = Field(..., description="A short summary of the actual data rows found")
    row_count: int = Field(..., description="The total number of rows combined from your queries")

def submit_final_report(report: DatabaseSummary) -> str:
    """ALWAYS call this tool to submit your final structured report."""
    return report.model_dump_json()

async def main():
    start_time = time.time()
    
    # 3. Connect to our CUSTOM Python MCP Server
    print("Starting custom MCP server subprocess...\n")
    mcp_client = BasicMCPClient(
        command="python", 
        args=["server.py"]
    )
    
    mcp_tool_spec = McpToolSpec(client=mcp_client)
    mcp_tools = await mcp_tool_spec.to_tool_list_async()
    
    structured_output_tool = FunctionTool.from_defaults(fn=submit_final_report)
    all_tools = mcp_tools + [structured_output_tool]

    # 4. Setup the FunctionAgent
    agent = FunctionAgent(
        name="CustomSQLiteAnalyst",
        tools=all_tools,
        llm=OpenAI(model="gpt-4o"),
        system_prompt=(
            "You are a meticulous database analyst. You interact with a database via MCP tools.\n"
            "1. Use `list_tables` to see what data is available.\n"
            "2. Use `run_query` to SELECT data and count rows.\n"
            "3. Finally, YOU MUST call `submit_final_report` to output your findings.\n"
            "Do not output raw conversational text as your final answer. Only output the tool result."
        )
    )

    prompt = "Check what tables exist, look at the data inside them, and give me a summary including the total row count."
    
    # 5. Execute the Agent and Wrap in StandardAPIResponse
    try:
        response = await agent.run(prompt)
        raw_json = response.response.content
        
        # Validate the LLM output against our schema
        final_summary = DatabaseSummary.model_validate_json(raw_json)
        
        processing_time = round((time.time() - start_time) * 1000)
        
        # Construct the success envelope
        api_response = StandardAPIResponse[DatabaseSummary](
            status="success",
            message="Database analysis completed successfully.",
            data=final_summary,
            metadata={"processing_time_ms": processing_time, "agent": "CustomSQLiteAnalyst"}
        )
        
        # Output the final standardized JSON payload
        print("--- Standardized API Response ---")
        print(api_response.model_dump_json(indent=2))

    except ValidationError as e:
        # Caught if the LLM hallucinated the output schema
        processing_time = round((time.time() - start_time) * 1000)
        error_response = StandardAPIResponse[DatabaseSummary](
            status="fail",
            message="Agent returned malformed data.",
            errors=e.errors(),
            metadata={"processing_time_ms": processing_time}
        )
        print("--- Standardized Error Response ---")
        print(error_response.model_dump_json(indent=2))
        
    except Exception as e:
        # Caught if the MCP server crashes, OpenAI fails, etc.
        processing_time = round((time.time() - start_time) * 1000)
        error_response = StandardAPIResponse[DatabaseSummary](
            status="error",
            message="An unexpected orchestration error occurred.",
            errors={"detail": str(e), "type": type(e).__name__},
            metadata={"processing_time_ms": processing_time}
        )
        print("--- Standardized Error Response ---")
        print(error_response.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
