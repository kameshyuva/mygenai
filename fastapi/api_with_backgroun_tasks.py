import asyncio
import contextvars

async def background_worker():
    # This will now successfully read the username
    user = username_ctx.get()
    print(f"Background work for {user}")

@app.post("/run-background")
async def run_in_background():
    # 1. Copy the current context (which contains your headers)
    ctx = contextvars.copy_context()
    
    # 2. Run the background task within that copied context
    asyncio.create_task(background_worker(), context=ctx)
    
    return {"status": "started"}
