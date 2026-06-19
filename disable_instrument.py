import llama_index.core.instrumentation as instrument

# This stops LlamaIndex from trying to pickle your workflow state for telemetry
instrument.root_dispatcher.span_handlers.clear()
instrument.root_dispatcher.event_handlers.clear()
