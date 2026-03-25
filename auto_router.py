import json
from typing import Optional, Dict, Any
from llama_index.embeddings.ollama import OllamaEmbedding
from redisvl.extensions.llmcache import SemanticCache
from redisvl.utils.vectorize import CustomTextVectorizer

class AutoTuningRouter:
    """
    A self-learning semantic router that caches ReAct agent decisions into Redis 
    to instantly route future, similar queries directly to the correct tool.
    """
    
    def __init__(
        self, 
        redis_url: str = "redis://localhost:6379", 
        embedding_model: str = "nomic-embed-text",
        distance_threshold: float = 0.20,
        cache_name: str = "dynamic_tool_router"
    ):
        print(f"Initializing AutoTuningRouter (Model: {embedding_model})...")
        
        # 1. Setup local embeddings
        self.embed_model = OllamaEmbedding(model_name=embedding_model)
        self.vectorizer = CustomTextVectorizer(embed=self.embed_model.get_text_embedding)
        
        # 2. Setup Redis Semantic Cache
        self.cache = SemanticCache(
            name=cache_name,
            redis_url=redis_url,
            distance_threshold=distance_threshold,
            vectorizer=self.vectorizer
        )

    def get_cached_tool(self, query: str) -> Optional[str]:
        """Checks Redis for a semantically similar query and returns the cached tool name."""
        cache_hit = self.cache.check(prompt=query)
        if cache_hit:
            return cache_hit[0]['response']
        return None

    def learn_route(self, query: str, tool_name: str) -> None:
        """Saves a successful user query -> tool mapping into Redis."""
        self.cache.store(prompt=query, response=tool_name)

    async def extract_arguments(self, query: str, tool_schema_str: str, llm) -> Dict[str, Any]:
        """
        Bypasses the ReAct loop and uses the LLM strictly as a fast JSON parser 
        to extract tool arguments from the user's query.
        """
        prompt = (
            f"Extract the arguments from this query: '{query}'\n"
            f"To fit this exact JSON schema: {tool_schema_str}\n"
            "Return ONLY valid JSON. Do not include markdown formatting or explanations."
        )
        
        response = await llm.acomplete(prompt)
        
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM failed to return valid JSON: {response.text}") from e
