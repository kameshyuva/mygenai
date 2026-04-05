from fastapi import Request
from context import username_ctx, realm_ctx, apptoken_ctx

async def header_context_middleware(request: Request, call_next):
    # 1. Extract headers (Note: HTTP headers in Starlette/FastAPI are lowercased)
    username = request.headers.get("x-username")
    realm = request.headers.get("x-realm")
    apptoken = request.headers.get("x-apptoken")

    # 2. Set the context variables and store the reset tokens
    t_username = username_ctx.set(username)
    t_realm = realm_ctx.set(realm)
    t_apptoken = apptoken_ctx.set(apptoken)

    try:
        # 3. Process the request
        response = await call_next(request)
        return response
    finally:
        # 4. Clean up / Reset the context variables
        username_ctx.reset(t_username)
        realm_ctx.reset(t_realm)
        apptoken_ctx.reset(t_apptoken)
