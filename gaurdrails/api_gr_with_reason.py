@app.post("/api/v1/agent/chat")
async def secure_chat(request: ChatRequest):
    # ... (assume input sanitization and generation happens here)
    final_text = "Here is the user's data: john.doe@email.com" 
    
    # Run the updated validation
    is_safe, failure_reason = await asyncio.to_thread(guardrails.validate_output, final_text)
    
    if not is_safe:
        # Instead of a generic 403, you now log or return exactly what Presidio found
        # e.g., {"detail": "Output blocked. Reason: PII Leak Detected: EMAIL_ADDRESS"}
        raise HTTPException(
            status_code=403, 
            detail=f"Output blocked. Reason: {failure_reason}"
        )
         
    return {"response": final_text}
