class AlertSummaryWorkflow(Workflow):
    
    # ... (previous steps: fetch_id and fetch_sensors) ...

    @step
    async def compile_summary(self, ev: SensorsFetchedEvent) -> StopEvent:
        """
        Takes the raw JSON sensor/alert data and the user's query,
        and uses an LLM to generate a plain-text summary.
        """
        # 1. Format the JSON payload for the LLM
        # Using indent=2 makes the JSON structure easier for the LLM's attention mechanism to parse
        alerts_data_json = json.dumps(ev.sensors, indent=2)
        
        # 2. Define the Prompt Template
        # This acts as the strict instruction set for how the LLM should handle the JSON
        prompt_tmpl = PromptTemplate(
            "You are an expert industrial diagnostic assistant.\n"
            "A user has asked the following question: '{query}'\n\n"
            "Here is the raw JSON data retrieved from the backend APIs regarding the asset's sensors and alerts:\n"
            "```json\n"
            "{json_data}\n"
            "```\n\n"
            "Based ONLY on the provided JSON data, answer the user's question. "
            "Format the active alerts clearly. Do not hallucinate data that is not in the JSON. "
            "Do not output raw JSON in your final response."
        )

        # 3. Inject the variables into the template
        formatted_prompt = prompt_tmpl.format(
            query=ev.user_query,
            json_data=alerts_data_json
        )

        # 4. Initialize your LLM
        # Using Ollama for local, efficient inference on this summarization task
        llm = Ollama(model="llama3", request_timeout=120.0)

        # 5. Execute the asynchronous completion call
        response = await llm.acomplete(formatted_prompt)

        # 6. Return the text response to complete the workflow and send to the Angular frontend
        return StopEvent(result=str(response))
