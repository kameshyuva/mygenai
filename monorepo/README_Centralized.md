ai-monorepo/
├── pyproject.toml              # Root workspace definition
│
├── api-gateway/                # NEW: The centralized API package
│   ├── pyproject.toml          # Dependencies: FastAPI, uvicorn, ARQ
│   ├── main.py                 # FastAPI initialization & Security Middleware
│   └── routers/
│       ├── agents.py           # Routes that trigger agent tasks
│       └── system.py           # Health checks and monitoring
│
├── agents-core/                # RENAMED: No longer contains an API
│   ├── pyproject.toml          # Dependencies: LlamaIndex, ARQ
│   ├── factory.py              # FunctionAgent instantiation
│   └── workers/
│       └── arq_tasks.py        # The ARQ workers that listen for jobs from the API
│
├── shared-libs/
└── mcp-servers/                
