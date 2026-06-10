import asyncio
from mcp.server.fastmcp import FastMCP

# 1. Initialize the FastMCP server
mcp = FastMCP("Facility Context Server")

# Mock asynchronous backend function (e.g., querying a database or internal API)
async def fetch_backend_context() -> dict:
    # Simulate network/DB latency
    await asyncio.sleep(0.1) 
    return {
        "active_site": "Houston Main",
        "active_plant": "Plant 1",
        "assets_in_view": ["Compressor C-2", "Pump P-105"]
    }

# 2. Expose the context as a standard Resource URI
@mcp.resource("app://context/current")
async def get_current_context() -> str:
    """Read-only resource providing the current application environment names."""
    
    # Fetch the raw data from your backend
    context_data = await fetch_backend_context()
    
    # Format the data cleanly. 
    # Returning a well-structured plain text string is highly token-efficient 
    # when this gets injected into the LLM's system prompt later.
    formatted_context = (
        f"Active Site: {context_data['active_site']}\n"
        f"Active Plant: {context_data['active_plant']}\n"
        f"Available Assets: {', '.join(context_data['assets_in_view'])}"
    )
    
    return formatted_context

if __name__ == "__main__":
    # Run the server. 
    # Use transport='stdio' for local processes or setup SSE for network access.
    mcp.run(transport='stdio') 
