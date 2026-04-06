from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from context import username_ctx, realm_ctx, apptoken_ctx

# --- 1. Custom Header Context Middleware ---
async def header_context_middleware(request: Request, call_next):
    username = request.headers.get("x-username")
    realm = request.headers.get("x-realm")
    apptoken = request.headers.get("x-apptoken")

    t_username = username_ctx.set(username)
    t_realm = realm_ctx.set(realm)
    t_apptoken = apptoken_ctx.set(apptoken)

    try:
        response = await call_next(request)
        return response
    finally:
        username_ctx.reset(t_username)
        realm_ctx.reset(t_realm)
        apptoken_ctx.reset(t_apptoken)


# --- 2. Master Setup Function ---
def setup_middlewares(app: FastAPI):
    """
    Registers all middlewares for the FastAPI app.
    Note: Middlewares are executed in the reverse order they are added.
    """
    
    # Register CORS Middleware (ASGI middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://your-frontend.com"], # Update with your domains
        allow_credentials=True,
        allow_methods=["*"],
        # CRITICAL: Ensure your custom headers are allowed by CORS
        allow_headers=["*", "x-username", "x-realm", "x-apptoken"], 
    )

    # Register Custom Context Middleware (HTTP middleware)
    app.middleware("http")(header_context_middleware)
