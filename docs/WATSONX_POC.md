# Watsonx Evaluation POC

This is a minimal proof-of-concept integration with IBM's watsonx governance evaluation library to understand the output structure and basic functionality.

## Setup

1. **Install the watsonx governance library:**
   ```bash
   pip install "ibm-watsonx-gov[agentic]"
   ```

2. **Activate your virtual environment** (remember the memory about this project):
   ```bash
   source .venv/bin/activate  # or however you activate your venv
   ```

## What This POC Does

- Creates a minimal custom agent (`watsonx_poc_agent`) that uses the watsonx evaluation library
- Evaluates prompt/response pairs with basic metrics (answer relevance, faithfulness)
- **Prints raw output structure** to understand what the library returns
- No database storage, no complex logging - just shows the data format

## Running the POC

### Option 1: Direct Python Test
```bash
cd /Users/gliu/Desktop/work/maestro
python tests/test_watsonx_poc.py
```

### Option 2: Maestro Workflow Test
```bash
cd /Users/gliu/Desktop/work/maestro
maestro run tests/yamls/agents/watsonx_poc_test.yaml tests/yamls/workflows/watsonx_poc_workflow.yaml
```

## Expected Output

The POC will show:

1. **Import status** - whether the watsonx library is available
2. **DataFrame structure** - shape, columns, data types
3. **Raw evaluation results** - actual metric values and formats  
4. **Error handling** - what happens when things go wrong

Example output structure:
```json
{
  "prompt": "What is quantum computing?",
  "response": "Quantum computing uses quantum phenomena...",
  "evaluation_available": true,
  "raw_dataframe_info": {
    "shape": [1, 8],
    "columns": ["interaction_id", "answer_relevance", "faithfulness", "latency", ...]
  },
  "raw_results": {
    "answer_relevance": 0.85,
    "faithfulness": 0.92,
    "latency": 2.3,
    "interaction_id": "poc_12345"
  }
}
```

## What We'll Learn

1. **Metric Names**: Exact field names the library returns
2. **Data Types**: Whether metrics are floats, ints, strings, etc.
3. **Data Structure**: How results are organized (DataFrame, dict, etc.)
4. **Error Modes**: What fails and how
5. **Performance**: How long evaluations take

## Next Steps

After understanding the output structure, we can:
1. Design proper database schema based on actual field names
2. Create automatic evaluation middleware 
3. Add proper error handling and logging
4. Integrate with existing Maestro infrastructure

## Files Created

- `src/maestro/agents/watsonx_poc_agent.py` - The POC agent
- `tests/test_watsonx_poc.py` - Direct test script
- `tests/yamls/agents/watsonx_poc_test.yaml` - Agent definition
- `tests/yamls/workflows/watsonx_poc_workflow.yaml` - Workflow test
- `src/maestro/agents/custom_agent.py` - Updated to include POC agent

