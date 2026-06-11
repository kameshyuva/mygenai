from fastapi import Depends, Header, HTTPException
from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

async def get_mcp_context(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Auth")

    # Pass the authorization header directly to the native SSE client
    headers = {"Authorization": authorization}

    # The official MCP SDK natively supports context managers for flawless cleanup
    async with sse_client("http://your-mcp-server.com/sse", headers=headers) as streams:
        # streams[0] is the read stream, streams[1] is the write stream
        async with ClientSession(streams[0], streams[1]) as session:
            # You must initialize the session before interacting with the server
            await session.initialize()
            
            # Fetch the resource
            result = await session.read_resource("app://context/current")
            
            # Safely extract all chunks (bypassing LlamaIndex's index-0 limitation)
            context_text = "\n".join(
                [chunk.text for chunk in result.contents if hasattr(chunk, 'text')]
            )
            
            # Yield the context to the FastAPI route handler
            yield context_text
            
            # Once the route returns the response, FastAPI resumes here.
            # Exiting the `async with` blocks automatically sends the teardown 
            # signals and safely closes the SSE transport.
