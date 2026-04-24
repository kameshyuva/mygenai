import json
from functools import wraps
from llama_index.core.tools import FunctionTool

# (Assuming json_to_markdown_list is defined as previously discussed)

def wrap_tool_for_markdown(original_tool: FunctionTool) -> FunctionTool:
    """Wraps an existing LlamaIndex tool to ensure its output is Markdown."""
    
    original_fn = original_tool.fn
    
    @wraps(original_fn)
    def wrapped_fn(*args, **kwargs):
        # 1. Execute the original MCP tool dynamically
        raw_result = original_fn(*args, **kwargs)
        
        # 2. Parse the output safely (MCP might return dicts, Pydantic models, or JSON strings)
        parsed_data = raw_result
        if hasattr(raw_result, "model_dump"):
            parsed_data = raw_result.model_dump()
        elif isinstance(raw_result, str):
            try:
                parsed_data = json.loads(raw_result)
            except json.JSONDecodeError:
                # If it's a plain string, just return it as is
                return raw_result
                
        # 3. Convert to Markdown to save context window tokens
        markdown_output = f"### Results for {original_tool.metadata.name}\n"
        markdown_output += json_to_markdown_list(parsed_data)
        
        return markdown_output

    # 4. Return a new tool that uses the wrapped function but keeps the original LLM schema
    return FunctionTool.from_defaults(
        fn=wrapped_fn,
        tool_metadata=original_tool.metadata,
        async_fn=original_tool.async_fn # Preserve async capabilities if you ever switch from .run()
    )
