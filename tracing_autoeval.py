import phoenix as px
from phoenix.evals import OpenAIModel, HallucinationEvaluator, run_evals
from phoenix.trace.dsl import SpanQuery

# 1. Connect to your active local Phoenix instance
client = px.Client()

# 2. Extract agent execution traces into a Pandas DataFrame
# We use Phoenix's domain-specific language (DSL) to grab the inputs and outputs of our Agent spans
query = SpanQuery().where(
    "span.kind == 'AGENT'"
).select(
    input="input.value",
    output="output.value",
)
spans_df = client.query_spans(query)

if spans_df.empty:
    print("No traces found. Run your LlamaIndex agent first!")
else:
    # 3. Configure your local Ollama model as the "Judge"
    # We point the standard OpenAI wrapper to Ollama's local endpoint
    eval_model = OpenAIModel(
        model="llama3", 
        base_url="http://localhost:11434/v1",
        api_key="ollama" # Required by the client structure, but safely ignored by Ollama
    )

    # 4. Set up the evaluator
    # Phoenix includes pre-built templates for Hallucination, QA Correctness, etc.
    evaluator = HallucinationEvaluator(eval_model)

    # 5. Run the evaluation
    print("Evaluating traces locally using Ollama...")
    
    # run_evals executes the prompt templates against your dataframe
    eval_results = run_evals(
        dataframe=spans_df,
        evaluators=[evaluator],
        provide_explanation=True,
    )

    # 6. Send the grades back to Phoenix
    # This attaches the scores and the LLM's reasoning directly to the traces in the UI
    from phoenix.trace import SpanEvaluations
    
    client.log_evaluations(
        SpanEvaluations(
            eval_name="Hallucination", 
            dataframe=eval_results[0]
        )
    )
    print("Done! Open your Phoenix dashboard to view the annotations.")
