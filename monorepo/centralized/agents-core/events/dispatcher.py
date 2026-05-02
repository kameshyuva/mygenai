import json
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

class AgentEventDispatcher:
    """
    Dynamically routes LlamaIndex AgentWorkflow events.
    Pass `type(event).__name__` as the event_name.
    """
    
    def process_event(self, event_name: str, event_data: Any) -> str:
        # e.g., "ToolCallResult" -> "handle_toolcallresult"
        method_name = f"handle_{event_name.lower()}"
        handler_method = getattr(self, method_name, self.handle_unknown)
        
        try:
            formatted_payload = handler_method(event_data)
            return self._format_sse(event_name, formatted_payload)
        except Exception as e:
            logger.error(f"Error formatting event {event_name}: {e}")
            return self._format_sse("error", {"detail": str(e)})

    def _format_sse(self, event_name: str, data: Dict[str, Any]) -> str:
        return f"event: {event_name}\ndata: {json.dumps(data)}\n\n"

    # ---------------------------------------------------------
    # Modern AgentWorkflow Event Handlers
    # ---------------------------------------------------------

    def handle_agentinput(self, event_data: Any) -> Dict[str, Any]:
        """Triggered when the agent receives the prompt."""
        # event.input is typically a list of ChatMessage objects
        messages = getattr(event_data, "input", [])
        last_msg = messages[-1].content if messages else ""
        
        return {
            "status": "processing",
            "agent_name": getattr(event_data, "current_agent_name", "unknown"),
            "query": last_msg
        }

    def handle_agentstream(self, event_data: Any) -> Dict[str, Any]:
        """Triggered as the LLM generates output tokens."""
        return {
            "token": getattr(event_data, "delta", "")
        }

    def handle_agentoutput(self, event_data: Any) -> Dict[str, Any]:
        """Triggered when the final response is complete."""
        # event_data.response contains the final AgentChatResponse
        return {
            "status": "complete"
        }

    def handle_toolcall(self, event_data: Any) -> Dict[str, Any]:
        """Triggered right before an MCP server or tool is invoked."""
        return {
            "status": "calling_tool",
            "tool_name": getattr(event_data, "tool_name", "unknown_tool"),
            "arguments": getattr(event_data, "tool_kwargs", {})
        }

    def handle_toolcallresult(self, event_data: Any) -> Dict[str, Any]:
        """
        Triggered when the tool returns data.
        Apply your token-efficient reduction/CSV flattening logic here.
        """
        tool_name = getattr(event_data, "tool_name", "unknown_tool")
        raw_output = getattr(event_data, "tool_output", getattr(event_data, "content", ""))
        
        # Example UI summary logic:
        summary_text = "Data processed."
        
        # In a real scenario, this is where you flatten your complex nested 
        # database payloads into CSV for the LLM to easily reason over.
        # For the frontend stream, we just send a brief summary so the UI doesn't freeze.
        if isinstance(raw_output, list) and len(raw_output) > 10:
            summary_text = f"Retrieved {len(raw_output)} records from {tool_name}."
        elif isinstance(raw_output, str):
            summary_text = raw_output[:100] + "..." if len(raw_output) > 100 else raw_output
            
        return {
            "status": "tool_executed",
            "tool_name": tool_name,
            "summary": summary_text
        }

    def handle_unknown(self, event_data: Any) -> Dict[str, Any]:
        logger.debug(f"Unmapped event type encountered: {type(event_data)}")
        return {"status": "processing_unknown_event"}
