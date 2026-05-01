ai-monorepo/
├── pyproject.toml              # 1. ROOT: Defines the workspace
│
├── agent-backend/              # The LlamaIndex API & Workers
│   ├── pyproject.toml          # 2. AGENT: Dependencies (LlamaIndex, FastAPI, ARQ)
│   ├── api/
│   ├── core/
│   ├── agents/                 # Contains your FunctionAgent logic
│   └── workers/                
│
├── shared-libs/                # Common schemas and telemetry (optional but recommended)
│   ├── pyproject.toml          # 3. SHARED: Pydantic models, trace configurations
│   └── src/
│
└── mcp-servers/                
    ├── alert_correlator/       # Specific MCP Server 1
    │   ├── pyproject.toml      # 4. MCP: Dependencies (mcp, sqlmodel)
    │   └── server.py
    │
    └── sensor_diagnostics/     # Specific MCP Server 2
        ├── pyproject.toml      # 5. MCP: Dependencies (mcp, redis)
        └── server.py
