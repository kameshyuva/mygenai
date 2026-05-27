mkdir models

# 1. Download the main Gemma 4 E4B model (e.g., Q4_K_M or Q8_0)
curl -L https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-Q4_K_M.gguf -o models/gemma-4-e4b.gguf

# 2. Download the matching MTP assistant drafter model
curl -L https://huggingface.co/AtomicChat/gemma-4-E4B-it-assistant-GGUF/resolve/main/gemma-4-E4B-it-assistant.Q4_K_M.gguf -o models/gemma-4-e4b-assistant.gguf
