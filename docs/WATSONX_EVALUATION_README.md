# Watsonx Evaluation Integration for Maestro

Maestro includes automatic evaluation capabilities using IBM's watsonx governance platform to assess agent response quality.

## Setup

### 1. Environment Setup
```bash
# Create Python 3.11 evaluation environment
python3.11 -m venv .venv-eval
source .venv-eval/bin/activate

# Install Maestro and watsonx evaluation library
uv pip install -e . --no-deps
uv pip install "ibm-watsonx-gov[agentic]==1.2.2"
```

### 2. API Key Configuration
Add your IBM watsonx API key to your `.env` file:
```bash
echo "WATSONX_APIKEY=your_api_key_here" >> .env
```

### 3. Enable Evaluation
```bash
export MAESTRO_AUTO_EVALUATION=true
```

## Usage

Run any workflow - evaluation happens automatically:
```bash
# Test with mock agent
maestro run tests/yamls/agents/evaluation_test_agent.yaml tests/yamls/workflows/evaluation_test_workflow.yaml

# Test with OpenAI agent  
maestro run tests/yamls/agents/openai_agent.yaml tests/yamls/workflows/openai_workflow.yaml
```

## Evaluation Metrics

| Metric | Description | Requires |
|--------|-------------|----------|
| Answer Relevance | How well response addresses the question | None |
| Faithfulness | How faithful response is to provided context | Context |
| Context Relevance | How relevant context is to the question | Context |
| Answer Similarity | Similarity to expected answer | Expected answer |

## Expected Output

```bash
✅ Maestro Auto Evaluation: Watsonx evaluator initialized
🔍 Maestro Auto Evaluation: Evaluating response from my-agent
📊 Maestro Auto Evaluation Summary for my-agent:
   ⏱️  Evaluation time: ~3–6s
   🎯 Watsonx Evaluation Scores:
      answer_relevance_score: 0.556 (token_recall via unitxt)
      faithfulness_score: 0.409 (token_k_precision via unitxt)
      context_relevance_score: 0.556 (token_precision via unitxt)
```

## Troubleshooting

- **Missing scores**: Verify `WATSONX_APIKEY` is set in `.env` file
- **Skipped metrics**: Provide `context` (list of strings) or `expected_answer` (string) as needed
- **Python version**: Evaluation requires Python 3.11 (use `.venv-eval` environment)

## Reference

- [IBM watsonx governance Agentic AI Evaluation SDK](https://dataplatform.cloud.ibm.com/docs/content/wsj/model/wxgov-agentic-ai-evaluation-sdk.html?context=wx&locale=en#examples)