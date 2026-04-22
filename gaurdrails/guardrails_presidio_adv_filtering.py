    def validate_output(self, text: str) -> Tuple[bool, str]:
        # Define PII types that are acceptable for your MCP tools to output
        ALLOWED_ENTITIES = ["PERSON", "LOCATION"]
        
        pii_results = self.analyzer.analyze(text=text, language='en')
        
        # Filter out the allowed entities
        critical_violations = [
            res.entity_type for res in pii_results 
            if res.entity_type not in ALLOWED_ENTITIES
        ]
        
        if critical_violations:
            unique_violations = list(set(critical_violations))
            reason = f"Critical PII Leak Detected: {', '.join(unique_violations)}"
            return False, reason
