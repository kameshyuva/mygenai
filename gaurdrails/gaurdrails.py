#pip install better_profanity presidio-analyzer presidio-anonymizer
#python -m spacy download en_core_web_lg 


import re
from typing import Optional
from better_profanity import profanity
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from llama_index.llms.ollama import Ollama

class SecurityViolationError(Exception):
    """Custom exception raised when input fails security validation."""
    pass

class AgentGuardrails:
    def __init__(self, semantic_model_name: str = "qwen3.5:0.5b", timeout: float = 30.0):
        # 1. Initialize deterministic filters
        profanity.load_censor_words()
        
        # 2. Initialize PII Engines (CPU-friendly via spaCy)
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # 3. Define injection blocklist
        self.injection_patterns = [
            r"(?i)ignore previous", 
            r"(?i)system prompt", 
            r"(?i)override",
            r"(?i)bypass"
        ]
        
        # 4. Initialize the lightweight semantic evaluator
        self.semantic_llm = Ollama(model=semantic_model_name, request_timeout=timeout)

    def sanitize_input(self, text: str) -> str:
        """
        Validates the input string against profanity and injection patterns.
        If safe, returns the string with PII redacted.
        Raises SecurityViolationError if malicious or inappropriate.
        """
        if not text:
            return ""

        # 1. Fast Profanity Check
        if profanity.contains_profanity(text):
            raise SecurityViolationError("Input contains inappropriate language.")

        # 2. Fast Injection Check
        for pattern in self.injection_patterns:
            if re.search(pattern, text):
                raise SecurityViolationError("Input violates safety policy.")

        # 3. PII Redaction
        analyzer_results = self.analyzer.analyze(text=text, language='en')
        anonymized_result = self.anonymizer.anonymize(
            text=text, 
            analyzer_results=analyzer_results
        )
        
        return anonymized_result.text

    def validate_output(self, text: str) -> bool:
        """
        Runs comprehensive checks on the LLM output.
        Returns True if the output is safe to show the user, False otherwise.
        """
        if not text:
            return False

        # 1. Check for generated profanity
        if profanity.contains_profanity(text):
            return False
            
        # 2. Check for leaked PII
        pii_results = self.analyzer.analyze(text=text, language='en')
        if len(pii_results) > 0:
            return False

        # 3. Semantic check via small local model (e.g., catching tracebacks)
        prompt = f"""
        Analyze the following text. Does it contain raw python code, tool traceback errors, 
        or system prompt instructions? Answer strictly YES or NO.
        Text: {text}
        """
        try:
            eval_result = self.semantic_llm.complete(prompt).text.strip().upper()
            return "YES" not in eval_result
        except Exception:
            # Fail closed: if the guardrail model times out or crashes, block the output
            return False
