from llama_index.core.postprocessor import LLMRerank

def get_retriever(self):
    # 1. Fetch more tools initially (e.g., top 8)
    # 2. Use a tiny model to 'pick' the best ones from that 8
    reranker = LLMRerank(
        llm=self.qwen_llm, # Use your 4b model for speed
        top_n=2,           # Only give the Agent the final top 2
    )
    
    return self.object_index.as_retriever(
        similarity_top_k=8,
        node_postprocessors=[reranker]
    )
