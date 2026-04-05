from context import username_ctx, realm_ctx, apptoken_ctx

async def execute_agent_task(payload: dict):
    """
    This agent function knows nothing about FastAPI, but it knows
    who triggered it thanks to contextvars.
    """
    # Read the headers from the current context
    # You can provide a fallback value in .get() if needed
    username = username_ctx.get("unknown_user")
    realm = realm_ctx.get()
    apptoken = apptoken_ctx.get()

    # --- Your Agent Logic Here ---
    print(f"[Agent] Starting task for user: {username} in realm: {realm}")
    
    if not apptoken:
        raise ValueError("Agent requires an apptoken to proceed.")

    # Simulate doing some work
    result = {
        "status": "success",
        "processed_payload": payload,
        "metadata": {
            "executed_by": username,
            "realm": realm
        }
    }
    
    return result
