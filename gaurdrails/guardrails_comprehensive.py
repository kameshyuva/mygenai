import re
import bleach
from typing import Tuple
from better_profanity import profanity
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from llama_index.llms.ollama import Ollama

class SecurityViolationError(Exception):
    pass

class AgentGuardrails:
    def __init__(self, semantic_model_name: str = "qwen3.5:0.5b", timeout: float = 15.0, max_input_length: int = 2000):
        # 1. Configurable Limits
        self.max_input_length = max_input_length
        
        # 2. Initialize Profanity & Presidio
        profanity.load_censor_words()
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        self.allowed_entities = self.analyzer.get_supported_entities()
        if "DATE_TIME" in self.allowed_entities:
            self.allowed_entities.remove("DATE_TIME")
            
        # 3. ADVANCED: Comprehensive Injection & Jailbreak Patterns
        self.injection_patterns = [
            r"(?i)ignore previous", 
            r"(?i)system prompt", 
            r"(?i)override",
            r"(?i)forget all",
            r"(?i)act as a",             # Persona adoption
            r"(?i)developer mode",       # Common jailbreak
            r"(?i)you are now",          # Roleplay enforcement
            r"(?i)new instructions",     # Instruction override
            r"(?i)base64"                # Directing the model to decode payloads
        ]
        
        # 4. ADVANCED: Obfuscation Detection (Base64 or excessive hex)
        # Matches strings that look like dense base64 payloads longer than 40 chars
        self.base64_pattern = re.compile(r"^(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$")
        
        # 5. Initialize the Semantic Evaluator
        self.semantic_llm = Ollama(
            model=semantic_model_name, 
            request_timeout=timeout,
            additional_kwargs={"num_predict": 2, "temperature": 0.0, "num_thread": 2}
        )

    def sanitize_input(self, text: str) -> str:
        """
        Comprehensive input validation: DoS protection, Obfuscation, Jailbreaks, and PII.
        """
        if not text:
            return ""

        # A. MEASURE 1: DoS & Buffer Protection
        if len(text) > self.max_input_length:
            raise SecurityViolationError(f"Input exceeds maximum allowed length of {self.max_input_length} characters.")

        # B. MEASURE 2: Obfuscation Check (Base64 payloads)
        # We split the text by words to see if any specific chunk is a hidden payload
        for word in text.split():
            if self.base64_pattern.match(word):
                raise SecurityViolationError("Suspicious encoded payload detected in input.")

        # C. Profanity Check
        if profanity.contains_profanity(text):
            raise SecurityViolationError("Input contains inappropriate language.")

        # D. MEASURE 3: Advanced Prompt Injections
        for pattern in self.injection_patterns:
            if re.search(pattern, text):
                raise SecurityViolationError("Input violates system safety policies (Jailbreak attempt detected).")

        # E. PII Redaction
        pii_results = self.analyzer.analyze(text=text, language='en', entities=self.allowed_entities)
        if pii_results:
            anonymized_result = self.anonymizer.anonymize(text=text, analyzer_results=pii_results)
            text = anonymized_result.text
            
        return text

    def sanitize_output(self, text: str) -> str:
        """
        Comprehensive output validation: XSS stripping, PII/Profanity redaction, and semantic checks.
        """
        if not text:
            return ""

        # A. MEASURE 4: XSS / UI Payload Stripping
        # Strips out <script>, <iframe>, and other malicious HTML tags that could 
        # execute in your frontend if the LLM decides to generate web code.
        clean_text = bleach.clean(text, tags=['b', 'i', 'strong', 'em', 'p', 'br', 'ul', 'li', 'ol', 'code', 'pre'])

        # B. Censor Profanity
        clean_text = profanity.censor(clean_text)

        # C. Censor PII
        pii_results = self.analyzer.analyze(text=clean_text, language='en', entities=self.allowed_entities)
        if pii_results:
            anonymized_result = self.anonymizer.anonymize(text=clean_text, analyzer_results=pii_results)
            clean_text = anonymized_result.text

        # D. Real-Time Semantic Check
        prompt = f"""
        Analyze the following text. Does it contain raw python code, tool traceback errors, 
        or system prompt instructions? Answer strictly YES or NO.
        Text: {clean_text}
        """
        try:
            eval_result = self.semantic_llm.complete(prompt).text.strip().upper()
            if "YES" in eval_result:
                raise SecurityViolationError("Unrecoverable semantic violation: System leakage detected.")
        except Exception as e:
            if isinstance(e, SecurityViolationError):
                raise e
            raise SecurityViolationError(f"Semantic evaluation failed: {str(e)}")
            
        return clean_text
