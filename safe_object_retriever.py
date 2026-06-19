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
