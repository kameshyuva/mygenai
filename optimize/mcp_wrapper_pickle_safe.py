import json
import csv
import io
from functools import wraps

# Define this at the absolute top level of your file
class JsonToCsvWrapper:
    """A pickle-safe decorator alternative that converts tool JSON outputs to CSV string."""
    def __init__(self, func):
        self.func = func
        # Keep the original function attributes intact for LlamaIndex
        wraps(func)(self)

    async def __call__(self, *args, **kwargs):
        # 1. Execute the underlying MCP tool function
        raw_response = await self.func(*args, **kwargs)
        
        # 2. Parse the JSON and extract into dense CSV
        try:
            # Handle if the response is already a string or dict/list
            data = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
            
            if not isinstance(data, list) or not data:
                return str(raw_response) # Fallback if not a list of rows
                
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(data[0].keys())
            # Write rows
            for item in data:
                writer.writerow(item.values())
                
            csv_string = output.getvalue()
            output.close()
            return csv_string
            
        except Exception:
            # Fallback if something fails during formatting so the agent doesn't crash
            return str(raw_response)
