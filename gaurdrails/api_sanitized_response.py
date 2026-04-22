@app.post("/api/v1/agent/chat")
async def secure_chat(request: ChatRequest):
    # ... (Input sanitization and agent execution)
    
    # Example of a messy response from the 9B model
    raw_final_text = "The assessment is done. The user's email is admin@company.com and this is absolutely f***ing broken."
    
    try:
        # Offload the CPU-intensive checks to a thread to keep the event loop free
        sanitized_text = await asyncio.to_thread(guardrails.sanitize_output, raw_final_text)
        
        # sanitized_text will now safely be: 
        # "The assessment is done. The user's email is <EMAIL_ADDRESS> and this is absolutely ****ing broken."
        return {"response": sanitized_text}
        
    except SecurityViolationError as e:
        # This is only triggered if the 0.5B model catches a traceback or prompt leak
        raise HTTPException(
            status_code=403, 
            detail=f"Output blocked. Reason: {str(e)}"
        )
