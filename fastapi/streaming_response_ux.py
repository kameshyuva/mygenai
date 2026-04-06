import json
from llama_index.core.agent.workflow import (
    AgentInput,
    AgentStream,
    ToolCall,
    ToolCallResult,
    AgentOutput
)

async def run_my_agent_stream(prompt: str, session_id: str):
    try:
        session_memory = get_memory_for_session(session_id)
        handler = global_agent.run(user_msg=prompt, memory=session_memory)
        
        async for event in handler.stream_events():
            
            # 1. AGENT STARTS THINKING
            if isinstance(event, AgentInput):
                payload = {
                    "type": "status", 
                    "message": f"Agent '{event.current_agent_name}' is thinking..."
                }
                yield f"data: {json.dumps(payload)}\n\n"
            
            # 2. AGENT DECIDES TO USE A TOOL
            elif isinstance(event, ToolCall):
                payload = {
                    "type": "tool_start",
                    "tool_name": event.tool_name,
                    # Convert kwargs dict to a readable string for the UI
                    "arguments": event.tool_kwargs 
                }
                yield f"data: {json.dumps(payload)}\n\n"
                
            # 3. TOOL FINISHES EXECUTING
            elif isinstance(event, ToolCallResult):
                payload = {
                    "type": "tool_finish",
                    "tool_name": event.tool_name,
                    # You can choose to send the output, or just a success flag
                    "status": "success" 
                }
                yield f"data: {json.dumps(payload)}\n\n"

            # 4. AGENT STREAMS TEXT (Filter out empty deltas)
            elif isinstance(event, AgentStream) and event.delta:
                payload = {
                    "type": "text_delta",
                    "content": event.delta
                }
                yield f"data: {json.dumps(payload)}\n\n"
            
            # 5. AGENT IS COMPLETELY DONE
            elif isinstance(event, AgentOutput):
                payload = {
                    "type": "agent_done",
                    "message": "Generation complete."
                }
                yield f"data: {json.dumps(payload)}\n\n"
                
        # Close the SSE connection gracefully
        yield f"data: {json.dumps({'type': 'stream_closed'})}\n\n"
        
    except Exception as e:
        error_payload = {"type": "error", "message": str(e)}
        yield f"data: {json.dumps(error_payload)}\n\n"
