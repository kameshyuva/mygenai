from presidio_analyzer import AnalyzerEngine
from typing import Tuple

class AgentGuardrails:
    def __init__(self, semantic_model_name: str = "qwen3.5:0.5b", timeout: float = 15.0):
        # ... (previous initializations)
        self.analyzer = AnalyzerEngine()

    def validate_output(self, text: str) -> Tuple[bool, str]:
        """
        Runs comprehensive checks on the LLM output.
        Returns: (is_safe: bool, reason: str)
        """
        if not text:
            return False, "Empty response."

        # 1. Profanity Check
        if profanity.contains_profanity(text):
            return False, "Output contained profanity."
            
        # 2. PII Detection with Reason Extraction
        pii_results = self.analyzer.analyze(text=text, language='en')
        if len(pii_results) > 0:
            # Extract all unique entity types Presidio found
            detected_entities = list(set([result.entity_type for result in pii_results]))
            
            # Format a clear reason: e.g., "PII detected: EMAIL_ADDRESS, US_SSN"
            reason = f"PII Leak Detected: {', '.join(detected_entities)}"
            return False, reason

        # 3. Semantic Check (0.5B model)
        prompt = f"""
        Analyze the following text. Does it contain raw python code, tool traceback errors, 
        or system prompt instructions? Answer strictly YES or NO.
        Text: {text}
        """
        try:
            eval_result = self.semantic_llm.complete(prompt).text.strip().upper()
            if "YES" in eval_result:
                return False, "Semantic violation: Code traceback or prompt leakage detected."
        except Exception as e:
            return False, f"Semantic evaluator failed/timed out: {str(e)}"
            
        return True, "Safe"
