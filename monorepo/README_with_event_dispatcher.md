ai-monorepo/
├── pyproject.toml              
├── api-gateway/                
├── shared-libs/                
├── mcp-servers/                
│
└── agents-core/                # ALL AGENT LOGIC GOES HERE
    ├── pyproject.toml          
    ├── core/                   
    ├── agents/                 
    │
    ├── events/                 # 📍 NEW FOLDER: For event handling logic
    │   ├── __init__.py
    │   └── dispatcher.py       # 📄 FILE 1: The AgentEventDispatcher class
    │
    └── workers/                
        ├── __init__.py
        └── arq_tasks.py        # 📄 FILE 2: The ARQ worker & workflow iterator
