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
        
        # We will use this to check if ANY text actually streamed
        streamed_any_text = False
        
        async for event in handler.stream_events():
            
            if isinstance(event, AgentInput):
                yield f"data: {json.dumps({'type': 'status', 'message': 'Thinking...'})}\n\n"
            
            elif isinstance(event, ToolCall):
                yield f"data: {json.dumps({'type': 'tool_start', 'tool_name': event.tool_name})}\n\n"
                
            elif isinstance(event, ToolCallResult):
                yield f"data: {json.dumps({'type': 'tool_finish', 'tool_name': event.tool_name})}\n\n"

            # 1. Attempt to stream text (if Ollama decides to cooperate)
            elif isinstance(event, AgentStream) and event.delta:
                streamed_any_text = True
                payload = {"type": "text_delta", "content": event.delta}
                yield f"data: {json.dumps(payload)}\n\n"
            
            # 2. THE FIX: Catch the final output
            elif isinstance(event, AgentOutput):
                # If AgentStream was completely empty due to Ollama buffering,
                # we extract the final generated string directly from the AgentOutput event.
                if not streamed_any_text:
                    # event.response is a ChatResponse object
                    final_text = event.response.message.content
                    
                    payload = {
                        "type": "full_text_response", 
                        "content": final_text
                    }
                    yield f"data: {json.dumps(payload)}\n\n"
                else:
                    # If it did stream properly, just send a standard completion flag
                    yield f"data: {json.dumps({'type': 'agent_done'})}\n\n"
                
        yield f"data: {json.dumps({'type': 'stream_closed'})}\n\n"
        
    except Exception as e:
        error_payload = {"type": "error", "message": str(e)}
        yield f"data: {json.dumps(error_payload)}\n\n"
