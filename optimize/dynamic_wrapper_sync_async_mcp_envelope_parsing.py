import json
from functools import wraps
from typing import Any
from llama_index.core.tools import FunctionTool

def json_to_markdown_list(data: Any, prefix: str = "") -> str:
    """Recursively flattens a JSON/dict object into a Markdown bulleted list."""
    markdown_lines = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                markdown_lines.append(f"{prefix}* **{key}**: ")
                markdown_lines.append(json_to_markdown_list(value, prefix + "  "))
            else:
                markdown_lines.append(f"{prefix}* **{key}**: {value}")
    elif isinstance(data, list):
        for index, item in enumerate(data):
            if isinstance(item, (dict, list)):
                markdown_lines.append(f"{prefix}* **Item {index + 1}**:")
                markdown_lines.append(json_to_markdown_list(item, prefix + "  "))
            else:
                markdown_lines.append(f"{prefix}* {item}")
    else:
         markdown_lines.append(f"{prefix}{data}")
            
    return "\n".join(markdown_lines)

def _process_raw_result_to_markdown(raw_result: Any, tool_name: str) -> str:
    """Unpacks the MCP envelope, parses the inner JSON, and converts strictly the result to Markdown."""
    inner_text = raw_result
    
    # 1. Unpack the MCP CallToolResult Envelope
    if hasattr(raw_result, "content") and isinstance(raw_result.content, list):
        if len(raw_result.content) > 0 and hasattr(raw_result.content[0], "text"):
            inner_text = raw_result.content[0].text
    elif isinstance(raw_result, dict) and "content" in raw_result:
         content_list = raw_result["content"]
         if isinstance(content_list, list) and len(content_list) > 0:
             inner_text = content_list[0].get("text", inner_text)

    # 2. Parse the extracted inner JSON string into a Python dictionary
    parsed_data = inner_text
    if isinstance(inner_text, str):
        try:
            parsed_data = json.loads(inner_text)
        except json.JSONDecodeError:
            parsed_data = inner_text
            
    # 3. Convert ONLY the extracted, parsed inner data to Markdown
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

    # 2. Wrap the ASYNCHRONOUS path
    wrapped_async_fn = None
    if original_async_fn:
        @wraps(original_async_fn)
        async def wrapped_async_fn_inner(*args, **kwargs):
            raw_result = await original_async_fn(*args, **kwargs)
            return _process_raw_result_to_markdown(raw_result, tool_name)
        
        wrapped_async_fn = wrapped_async_fn_inner

    # 3. Return the new tool with BOTH paths secured and original schema preserved
    return FunctionTool.from_defaults(
        fn=wrapped_fn,
        async_fn=wrapped_async_fn, 
        tool_metadata=original_tool.metadata,
    )
