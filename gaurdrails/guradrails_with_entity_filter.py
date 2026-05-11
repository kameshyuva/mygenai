import re
from typing import Tuple
from better_profanity import profanity
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from llama_index.llms.ollama import Ollama

class SecurityViolationError(Exception):
    """Custom exception raised when an unrecoverable security violation occurs."""
    pass

class AgentGuardrails:
    def __init__(self, semantic_model_name: str = "qwen3.5:0.5b", timeout: float = 15.0):
        # 1. Initialize Profanity Checker
        profanity.load_censor_words()
        
        # 2. Initialize Presidio Engines
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # 3. Configure PII Entities (Keep DATE_TIME intact for business context)
        self.allowed_entities = self.analyzer.get_supported_entities()
        if "DATE_TIME" in self.allowed_entities:
            self.allowed_entities.remove("DATE_TIME")
            
        # 4. Define Prompt Injection Blocklist
        self.injection_patterns = [
            r"(?i)ignore previous", 
            r"(?i)system prompt", 
            r"(?i)override",
            r"(?i)bypass",
            r"(?i)forget all"
        ]
        
        # 5. Initialize the Semantic Evaluator (Optimized for <500ms Real-Time Execution)
        # We force temperature to 0 and max tokens to 2 because we only need a YES/NO.
        self.semantic_llm = Ollama(
            model=semantic_model_name, 
            request_timeout=timeout,
            additional_kwargs={
                "num_predict": 2,    # Stop generating immediately after outputting "YES" or "NO"
                "temperature": 0.0,  # Absolute determinism
                "num_thread": 2      # Use minimal CPU threads so the 9B model isn't starved
            }
        )

    def sanitize_input(self, text: str) -> str:
        """
        Validates the user input. Blocks malicious intents and redacts PII.
        Raises SecurityViolationError if completely unacceptable.
        """
        if not text:
            return ""

        # A. Block Profane Inputs
        if profanity.contains_profanity(text):
            raise SecurityViolationError("Input contains inappropriate language.")

        # B. Block Prompt Injections
        for pattern in self.injection_patterns:
            if re.search(pattern, text):
                raise SecurityViolationError("Input violates system safety policies.")

        # C. Redact PII (Ignores DATE_TIME based on init config)
        pii_results = self.analyzer.analyze(
            text=text, 
            language='en', 
            entities=self.allowed_entities
        )
        
        if pii_results:
            anonymized_result = self.anonymizer.anonymize(
                text=text, 
                analyzer_results=pii_results
            )
            return anonymized_result.text
            
        return text

    def sanitize_output(self, text: str) -> str:
        """
        Actively redacts PII and profanity from the LLM output.
        Runs a final semantic check and raises an error ONLY if an un-redactable 
        leak (like code tracebacks) is detected.
        """
        if not text:
            return ""

        # A. Censor Profanity (Replaces with ****)
        clean_text = profanity.censor(text)

        # B. Censor PII (Replaces with tags like <EMAIL_ADDRESS>)
        pii_results = self.analyzer.analyze(
            text=clean_text, 
            language='en', 
            entities=self.allowed_entities
        )
        
        if pii_results:
            anonymized_result = self.anonymizer.anonymize(
                text=clean_text, 
                analyzer_results=pii_results
            )
            clean_text = anonymized_result.text

        # C. Real-Time Semantic Check (0.5B Model)
        # We run this on the PII-scrubbed text to ensure system traces aren't leaking.
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
            # Fail-closed mechanism: If Ollama crashes or times out, block the output.
            if isinstance(e, SecurityViolationError):
                raise e
            raise SecurityViolationError(f"Semantic evaluation failed/timed out: {str(e)}")
            
        return clean_text

    def validate_output_reason(self, text: str) -> Tuple[bool, str]:
        """
        A purely diagnostic method. Does not sanitize, but returns a boolean and 
        the exact reason for failure. Useful for backend logging or async auditing.
        """
        if profanity.contains_profanity(text):
            return False, "Output contained profanity."
            
        pii_results = self.analyzer.analyze(text=text, language='en', entities=self.allowed_entities)
        if pii_results:
            detected_entities = list(set([res.entity_type for res in pii_results]))
            return False, f"PII Leak Detected: {', '.join(detected_entities)}"

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
            return False, f"Semantic evaluator failed: {str(e)}"
            
        return True, "Safe"
