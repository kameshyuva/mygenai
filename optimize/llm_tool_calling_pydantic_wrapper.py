import inspect
from pydantic import ValidationError
from llama_index.core.tools import FunctionTool

class HintDrivenMCPTool(FunctionTool):
    def call(self, *args, **kwargs):
        # If the LLM outputs flat arguments (missing the "request" envelope)
        if "request" not in kwargs:
            sig = inspect.signature(self._fn)
            
            # Ensure the tool actually has a parameter named 'request'
            if "request" in sig.parameters:
                # 1. Extract the type hint (your Pydantic model)
                pydantic_model = sig.parameters["request"].annotation
                
                try:
                    # 2. Enforce validation using the type hint
                    validated_request = pydantic_model(**kwargs)
                    
                    # 3. Hydrate the expected envelope
                    kwargs = {"request": validated_request}
                except ValidationError as e:
                    # Catch the Pydantic error and return it as a string
                    # This allows the LlamaIndex agent loop to see the error 
                    # and potentially prompt Gemma to fix its mistake.
                    return f"Tool Argument Validation Error:\n{e}"
                
        return super().call(*args, **kwargs)

    async def acall(self, *args, **kwargs):
        if "request" not in kwargs:
            sig = inspect.signature(self._async_fn or self._fn)
            if "request" in sig.parameters:
                pydantic_model = sig.parameters["request"].annotation
                try:
                    validated_request = pydantic_model(**kwargs)
                    kwargs = {"request": validated_request}
                except ValidationError as e:
                    return f"Tool Argument Validation Error:\n{e}"
                
        return await super().acall(*args, **kwargs)

# Usage remains exactly the same, but you use your custom class:
# my_tool = HintDrivenMCPTool.from_defaults(fn=my_pure_mcp_tool)
