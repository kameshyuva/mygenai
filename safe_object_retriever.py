from llama_index.core.objects import ObjectRetriever

# 1. Create a subclass that overrides the deepcopy behavior
class SafeObjectRetriever(ObjectRetriever):
    def __deepcopy__(self, memo):
        # When LlamaIndex tries to copy this, just return the exact same 
        # object in memory. This protects the live MCP connection locks!
        return self

# 2. Wrap your fusion retriever with this new safe class
ensemble_tool_retriever = SafeObjectRetriever(
    retriever=fusion_retriever,
    object_node_mapping=obj_index._object_node_mapping
)

# 3. Pass it to your agent
agent_worker = FunctionCallingAgentWorker(
    tool_retriever=ensemble_tool_retriever,
    llm=your_llm, # Make sure this is the LLM instance, not the module!
    verbose=True
)
agent = agent_worker.as_agent()


import types

# 1. Initialize your BM25 Retriever as usual
bm25_retriever = BM25Retriever.from_defaults(
    nodes=tool_nodes,
    similarity_top_k=3
)

# 2. Patch the instance to block deepcopying the compiled C objects
bm25_retriever.__deepcopy__ = types.MethodType(lambda self, memo: self, bm25_retriever)

# 3. Proceed with your Fusion Retriever
fusion_retriever = QueryFusionRetriever(
    retrievers=[vector_retriever, bm25_retriever], # BM25 is now protected!
    similarity_top_k=3,
    num_queries=1,
    mode="reciprocal_rerank",
)

# 4. Wrap with your SafeObjectRetriever and pass to the Agent
ensemble_tool_retriever = SafeObjectRetriever(
    retriever=fusion_retriever,
    object_node_mapping=obj_index._object_node_mapping
)


import types

# 1. Get your tools from MCP
mcp_tools = mcp_spec.to_tool_list()

# 2. SHIELD THE TOOLS: Prevent LlamaIndex from copying the live MCP client functions
for tool in mcp_tools:
    tool.__deepcopy__ = types.MethodType(lambda self, memo: self, tool)

# 3. Proceed with building your ObjectIndex
obj_index = ObjectIndex.from_objects(
    mcp_tools,
    index_cls=VectorStoreIndex,
)
