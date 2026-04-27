import json
from functools import wraps
from llama_index.core.tools import FunctionTool

# (Assuming your json_to_markdown_list helper is defined)

def _process_raw_result_to_markdown(raw_result, tool_name: str) -> str:
    """Helper function to parse and format the output for both sync and async wrappers."""
    parsed_data = raw_result
    
    # Handle Pydantic models or MCP specific objects
    if hasattr(raw_result, "model_dump"):
        parsed_data = raw_result.model_dump()
    elif isinstance(raw_result, str):
        try:
            parsed_data = json.loads(raw_result)
        except json.JSONDecodeError:
            return raw_result # Return as-is if it's already a plain string
            
    markdown_output = f"### Results for {tool_name}\n"
    markdown_output += json_to_markdown_list(parsed_data)
    return markdown_output

def wrap_tool_for_markdown(original_tool: FunctionTool) -> FunctionTool:
    """Wraps an existing LlamaIndex tool to ensure its output is Markdown, handling both sync and async."""
    
    original_fn = original_tool.fn
    original_async_fn = original_tool.async_fn
    tool_name = original_tool.metadata.name
    
    # 1. Wrap the SYNCHRONOUS path
    @wraps(original_fn)
    def wrapped_fn(*args, **kwargs):
        raw_result = original_fn(*args, **kwargs)
        return _process_raw_result_to_markdown(raw_result, tool_name)

    # 2. Wrap the ASYNCHRONOUS path (This is the critical fix)
    wrapped_async_fn = None
    if original_async_fn:
        @wraps(original_async_fn)
        async def wrapped_async_fn_inner(*args, **kwargs):
            raw_result = await original_async_fn(*args, **kwargs)
            return _process_raw_result_to_markdown(raw_result, tool_name)
        
        wrapped_async_fn = wrapped_async_fn_inner

    # 3. Return the new tool with BOTH paths secured
    return FunctionTool.from_defaults(
        fn=wrapped_fn,
        async_fn=wrapped_async_fn, 
        tool_metadata=original_tool.metadata,
    )
