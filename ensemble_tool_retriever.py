#pip install llama-index-retrievers-bm25

from llama_index.core.objects import ObjectIndex
from llama_index.core import VectorStoreIndex
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.schema import QueryBundle

# 1. Fetch your tools from the MCP Tool Spec
# Assuming mcp_spec is your McpToolSpec instance
mcp_tools = mcp_spec.to_tool_list()

# 2. Create the standard ObjectIndex (This builds the Vector Index)
obj_index = ObjectIndex.from_objects(
    mcp_tools,
    index_cls=VectorStoreIndex,
)

# 3. Extract the underlying text nodes (tool descriptions)
vector_index = obj_index._index
tool_nodes = list(vector_index.docstore.docs.values())

# 4. Initialize the BM25 Retriever for exact keyword matching
bm25_retriever = BM25Retriever.from_defaults(
    nodes=tool_nodes,
    similarity_top_k=3 # Adjust based on how many tools you want to fetch
)

# 5. Initialize the Vector Retriever
vector_retriever = vector_index.as_retriever(similarity_top_k=3)

# 6. Fuse the retrievers using Reciprocal Rank Fusion (RRF)
fusion_retriever = QueryFusionRetriever(
    retrievers=[vector_retriever, bm25_retriever],
    similarity_top_k=3,
    num_queries=1, # Keep at 1 to prevent the LLM from trying to rewrite the query, saving latency
    mode="reciprocal_rerank",
)

# 7. Create a custom Tool Retriever wrapper for your Agent
class EnsembleToolRetriever:
    def __init__(self, fusion_retriever, object_node_mapping):
        self.fusion_retriever = fusion_retriever
        self.object_node_mapping = object_node_mapping

    def retrieve(self, str_or_query_bundle):
        if isinstance(str_or_query_bundle, str):
            str_or_query_bundle = QueryBundle(str_or_query_bundle)
            
        # Retrieve the fused nodes
        nodes = self.fusion_retriever.retrieve(str_or_query_bundle)
        
        # Map the retrieved text nodes back to the executable BaseTool objects
        tools = []
        for node_with_score in nodes:
            tool = self.object_node_mapping.from_node(node_with_score.node)
            tools.append(tool)
            
        return tools

# 8. Instantiate your new Ensemble Tool Retriever
ensemble_tool_retriever = EnsembleToolRetriever(
    fusion_retriever=fusion_retriever,
    object_node_mapping=obj_index._object_node_mapping
)

# 9. Pass it to your FunctionAgent!
# agent = FunctionCallingAgentWorker(
#     tool_retriever=ensemble_tool_retriever,
#     llm=your_llm,
#     ...
# ).as_agent()
