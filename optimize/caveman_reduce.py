import re

def enhanced_caveman_reduce(text: str) -> str:
    """
    Strips conversational fluff and safe filler words from a prompt
    while strictly preserving semantic intent and negations.
    """
    # 1. Greetings & Pleasantries
    pleasantries = r"\b(hello|hi|hey|greetings|good morning|good afternoon|thanks|thank you|please|kindly|appreciate it)\b"
    
    # 2. Request Wrappers (Instructional fluff)
    # We strip the "asking" part because the LLM is already instructed to answer.
    wrappers = r"\b(can you|could you|would you|would you mind|i would like to know|tell me|show me|give me|find out|i need you to|please provide|help me with|let me know|figure out|just|simply)\b"
    
    # 3. Safe Fillers (Articles and basic "to be" verbs)
    # CRITICAL: We DO NOT include negations (not, never, no, lacking, without) 
    # or conjunctions (and, or, but, if) because they dictate logic.
    fillers = r"\b(the|a|an|some|any|is|are|am|was|were|will|do|does|did|to|of)\b"
    
    # Combine patterns
    patterns = [pleasantries, wrappers, fillers]
    
    reduced = text
    for pattern in patterns:
         # Replace matches with a space (case-insensitive)
        reduced = re.sub(pattern, ' ', reduced, flags=re.IGNORECASE)
        
    # 4. Punctuation Cleanup
    # Users often leave hanging question marks or commas after fluff is removed.
    # We keep hyphens, underscores, and periods (important for asset_ids, IPs, etc.)
    reduced = re.sub(r'[\?\,\!]+', ' ', reduced)
    
    # 5. Collapse multiple spaces into one
    reduced = re.sub(r'\s+', ' ', reduced).strip()
    
    return reduced

# --- Example Usage ---
# Original: "Hello, could you please find out what the severity is for the alert on asset_id 99-A? Thanks!"
# Reduced:  "what severity for alert on asset_id 99-A"
