# API Options for Agentic Tool Calling & Routing
options = {
    # --- Determinism & Strict Syntax Filters ---
    "temperature": 0.1,        # Near-zero to prevent creative deviations in structured outputs.
    "top_k": 10,               # Hard cap on vocabulary to prevent hallucinated keys or invalid tool names.
    "top_p": 0.5,              # Aggressive nucleus sampling to strictly favor high-probability tokens.
    "min_p": 0.05,             # Drops any token with <5% probability relative to the most likely token.
    "repeat_penalty": 1.0,     # CRITICAL: Must be 1.0 (disabled) so the model does not aggressively avoid repeating JSON braces, commas, and structural syntax.
    "seed": 42,                # Locks the random number generator for perfectly predictable, testable routing outputs.
    
    # --- Hardware & Execution Optimizations ---
    "num_thread": 6,           # Binds to physical cores while intentionally leaving 2 cores entirely free to process background task queues and logging without contention.
    
    # --- Memory & Cache Management ---
    "num_ctx": 4096,           # Strict context cap to prevent the KV cache from ballooning during prolonged autonomous loops.
    "num_batch": 1024          # Leverages available system RAM to rapidly digest large tool schemas and system instructions in larger chunks.
}
