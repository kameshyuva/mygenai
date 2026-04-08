# Import the synthesizer class we created earlier
from synthesizer import LlamaIndexSynthesizer

# You can initialize this globally or inside your class to reuse the Ollama connection
data_synthesizer = LlamaIndexSynthesizer(model_name="mistral")

async def your_existing_agent_generator(user_prompt: str):
    """
    Your current generator that already handles AgentInput, ToolCall, etc.
    """
    full_synthesized_text = ""
    
    # ... [Your existing code yielding AgentInput and ToolCall] ...

    # 1. Tool Execution Phase
    # You get your data from the BasicMcpClient
    mcp_raw_json = await mcp_client.execute_tool(...)
    
    # You yield your existing ToolCallResult event
    yield stream_event("ToolCallResult", {"raw_data": mcp_raw_json})

    # ---------------------------------------------------------
    # NEW SYNTHESIS BLOCK
    # ---------------------------------------------------------
    
    # 2. Pass the user prompt and the MCP JSON to the synthesizer
    chunk_stream = data_synthesizer.stream_synthesis(
        query=user_prompt, 
        raw_data=mcp_raw_json
    )

    # 3. Consume the LlamaIndex stream and yield AgentStream events
    async for chunk in chunk_stream:
        full_synthesized_text += chunk
        # Yield each token to your Angular frontend as it arrives from Ollama
        yield stream_event("AgentStream", {"chunk": chunk})

    # 4. Yield the final aggregated output
    yield stream_event("AgentOutput", {"full_text": full_synthesized_text})

    # ---------------------------------------------------------
    
    # ... [Your existing code yielding the "done" event] ...
