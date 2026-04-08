import json
from typing import AsyncGenerator
# from your_module import stream_event
from synthesizer import LlamaIndexSynthesizer

# Initialize the synthesizer globally to keep the Ollama connection warm
data_synthesizer = LlamaIndexSynthesizer(model_name="mistral")

async def chat_handler(user_prompt: str) -> AsyncGenerator[str, None]:
    """
    Consumes the FunctionAgent stream, captures tool data, 
    and appends the LlamaIndex synthesis at the end.
    """
    
    # 1. Initialize your agent handler
    handler = agent.run(user_prompt)
    
    # Variables to hold state during the stream
    captured_mcp_data = []
    full_synthesized_text = ""

    # 2. Iterate through your existing agent events
    async for event in handler.stream_events():
        # Assuming your event object has .type and .data attributes (or is a dict)
        # Adjust the access pattern (e.g., event["type"]) if it is a dictionary
        event_type = getattr(event, "type", event.get("type"))
        event_data = getattr(event, "data", event.get("data", {}))

        # Pass the event directly to the frontend so the UI updates
        yield stream_event(event_type, event_data)

        # INTERCEPT: If this is the tool result, grab the raw JSON data
        if event_type == "ToolCallResult":
            # Extract the raw JSON based on how your MCP client formats the result
            captured_mcp_data = event_data.get("raw_data", [])

    # 3. Trigger Synthesis AFTER the agent finishes its routing/tool loop
    if captured_mcp_data:
        # Optional: Let the frontend know synthesis is starting
        yield stream_event("status", {"message": "Synthesizing data with Ollama..."})

        # Run the LlamaIndex synthesis using the captured MCP data
        chunk_stream = data_synthesizer.stream_synthesis(
            query=user_prompt, 
            raw_data=captured_mcp_data
        )

        # 4. Stream the chunks to the frontend
        async for chunk in chunk_stream:
            full_synthesized_text += chunk
            yield stream_event("AgentStream", {"chunk": chunk})

        # 5. Yield the final synthesized output
        yield stream_event("AgentOutput", {"full_text": full_synthesized_text})
        
    else:
        # Fallback if the agent didn't call any tools or returned no data
        fallback_msg = "No data was retrieved from the tools to synthesize."
        yield stream_event("AgentOutput", {"full_text": fallback_msg})

    # 6. Signal that the entire connection is complete
    yield stream_event("done", {"status": "complete"})
