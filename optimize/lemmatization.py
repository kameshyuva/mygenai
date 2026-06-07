# Add via uv: uv add pyinflect
import spacy
import pyinflect 

# Use the model you're already loading for Presidio
nlp = spacy.load("en_core_web_lg") 

def get_dynamic_status_spacy(tool_name: str) -> str:
    parts = tool_name.split("_")
    verb_text = parts[0]
    rest = " ".join(parts[1:])
    
    # 1. Process the verb through your existing spaCy model
    token = nlp(verb_text)[0]
    
    # 2. Use the ._.inflect extension (VBG = Gerund/Present Participle)
    gerund = token._.inflect("VBG")
    
    return f"{gerund} {rest}".strip()

# Example: "get_business_alerts" -> "getting business alerts"
