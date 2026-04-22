from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from better_profanity import profanity
from typing import Tuple

class SecurityViolationError(Exception):
    pass

class AgentGuardrails:
    def __init__(self, semantic_model_name: str = "qwen3.5:0.5b", timeout: float = 15.0):
        profanity.load_censor_words()
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        # ... (Ollama initialization)

    def sanitize_output(self, text: str) -> str:
        """
        Actively redacts PII and profanity from the LLM output.
        Raises an error ONLY if an un-redactable semantic leak is detected.
        """
        if not text:
            return ""

        # 1. Sanitize Profanity (Replaces bad words with ****)
        clean_text = profanity.censor(text)

        # 2. Sanitize PII (Replaces entities with tags like <EMAIL_ADDRESS>)
        # You can pass your ALLOWED_ENTITIES list here if you want to skip redacting names/locations
        pii_results = self.analyzer.analyze(text=clean_text, language='en')
        
        if len(pii_results) > 0:
            anonymized_result = self.anonymizer.anonymize(
                text=clean_text, 
                analyzer_results=pii_results
            )
            clean_text = anonymized_result.text

        # 3. Semantic Check (0.5B model)
        # We run this ON THE CLEAN TEXT. If the model generated a traceback, 
        # it is too complex to cleanly redact without breaking formatting, so we block.
        prompt = f"""
        Analyze the following text. Does it contain raw python code, tool traceback errors, 
        or system prompt instructions? Answer strictly YES or NO.
        Text: {clean_text}
        """
        try:
            eval_result = self.semantic_llm.complete(prompt).text.strip().upper()
            if "YES" in eval_result:
                raise SecurityViolationError("Unrecoverable semantic violation: Code traceback or prompt leakage detected.")
        except Exception as e:
            # Fail closed on semantic model failure
            raise SecurityViolationError(f"Semantic evaluator failed: {str(e)}")
            
        return clean_text
