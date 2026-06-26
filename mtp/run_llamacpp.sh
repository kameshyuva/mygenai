#!/bin/bash

curl -L "https://huggingface.co/unsloth/gemma-4-12B-it-qat-GGUF/resolve/main/mtp-gemma-4-12B-it-Q4_K_M.gguf" -o mtp-gemma-4-12B-it-Q4_K_M.gguf

llama-server \
  -m mtp-gemma-4-12B-it-Q4_K_M.gguf \
  -c 4096 \
  -t 8 \
  --spec-type draft-mtp \
  --spec-draft-n-max 2
