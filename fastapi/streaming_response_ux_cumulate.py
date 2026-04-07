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
        
        # 1. Create an accumulator variable to hold the chunks
        accumulated_json_string = ""
        
        async for event in handler.stream_events():
            
            if isinstance(event, AgentInput):
                yield f"data: {json.dumps({'type': 'status', 'message': 'Thinking...'})}\n\n"
            
            elif isinstance(event, ToolCall):
                yield f"data: {json.dumps({'type': 'tool_start', 'tool_name': event.tool_name})}\n\n"
                
            elif isinstance(event, ToolCallResult):
                yield f"data: {json.dumps({'type': 'tool_finish', 'tool_name': event.tool_name})}\n\n"

            # 2. ACCUMULATE INSTEAD OF YIELDING
            elif isinstance(event, AgentStream) and event.delta:
                # Add the chunk to our full string, but DO NOT send it to the frontend yet
                accumulated_json_string += event.delta
            
            # 3. SEND THE FULL OBJECT WHEN FINISHED
            elif isinstance(event, AgentOutput):
                try:
                    # Optional: Verify it's valid JSON before sending
                    # This ensures you don't send malformed text to your frontend
                    parsed_json_object = json.loads(accumulated_json_string)
                    
                    payload = {
                        "type": "full_json_response",
                        "content": parsed_json_object # Send as a structured dictionary
                    }
                except json.JSONDecodeError:
                    # Fallback if the LLM hallucinated and didn't output strict JSON
                    payload = {
                        "type": "full_text_response",
                        "content": accumulated_json_string
                    }
                
                # Yield the final, complete payload
                yield f"data: {json.dumps(payload)}\n\n"
                
        yield f"data: {json.dumps({'type': 'stream_closed'})}\n\n"
        
    except Exception as e:
        error_payload = {"type": "error", "message": str(e)}
        yield f"data: {json.dumps(error_payload)}\n\n"
