import json
from typing import Union, Dict, List
from llama_index.core import PromptTemplate
from llama_index.core.llms.llm import LLM

class JSONDataSummarizer:
    """
    A reusable utility class to summarize raw JSON data against a user query using an LLM.
    """
    def __init__(self, llm: LLM, custom_prompt: str = None):
        self.llm = llm
        
        # Default prompt optimized for industrial/alert data
        default_prompt = (
            "You are an expert industrial diagnostic assistant.\n"
            "A user has asked the following question: '{query}'\n\n"
            "Here is the raw JSON data retrieved from the backend APIs:\n"
            "```json\n"
            "{json_data}\n"
            "```\n\n"
            "Based ONLY on the provided JSON data, answer the user's question. "
            "Format the active alerts clearly. Do not hallucinate data that is not in the JSON. "
            "Do not output raw JSON in your final response."
        )
        
        # Allow overriding the prompt if needed for other use cases
        template_str = custom_prompt if custom_prompt else default_prompt
        self.prompt_tmpl = PromptTemplate(template_str)

    async def generate_summary(self, query: str, data: Union[Dict, List, str]) -> str:
        """
        Takes the user query and raw data, formats it, and calls the LLM.
        """
        # Ensure the data is a nicely formatted JSON string
        if isinstance(data, (dict, list)):
            json_string = json.dumps(data, indent=2)
        else:
            json_string = str(data)

        # Inject into the template
        formatted_prompt = self.prompt_tmpl.format(
            query=query,
            json_data=json_string
        )

        # Execute completion
        response = await self.llm.acomplete(formatted_prompt)
        return str(response)
