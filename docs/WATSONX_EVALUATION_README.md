# Watsonx Evaluation Integration for Maestro

Maestro includes automatic evaluation capabilities using IBM's watsonx governance platform to assess agent response quality.

## Setup

### 1. Environment Setup

**Complete Step-by-Step Process**

Follow these exact commands to set up a working evaluation environment:

```bash
# Step 1: Create Python 3.11 evaluation environment
python3.11 -m venv .venv-eval
source .venv-eval/bin/activate

# Step 2: Install Maestro with all dependencies (includes beeai-framework)
uv pip install -e .

# Step 3: Install watsonx evaluation library
uv pip install "ibm-watsonx-gov[agentic]==1.2.2"

# Step 4: CRITICAL - Pin compatible versions to resolve conflicts
uv pip install "openai==1.98.0" "openai-agents==0.2.5" "litellm==1.72.0"
```

**Expected Result**:
After these steps, you should have:
- ✅ **Maestro working** with all agent types
- ✅ **Evaluation functionality** fully operational
- ✅ **All evaluation metrics** working (Answer Relevance, Faithfulness, Context Relevance)
- ✅ **Both mock and OpenAI agents** compatible with evaluation

**Why This Works**:
The version pinning in Step 4 forces compatible versions that satisfy both `ibm-watsonx-gov` and `openai-agents` requirements, avoiding the dependency conflict that occurs with default dependency resolution.

**Verification**:
After completing all steps, verify your setup works:
```bash
# Test evaluation with mock agent
export MAESTRO_AUTO_EVALUATION=true
maestro run tests/yamls/agents/evaluation_test_agent.yaml tests/yamls/workflows/evaluation_test_workflow.yaml
```

You should see:
- ✅ Maestro Auto Evaluation: Watsonx evaluator initialized
- ✅ Evaluation scores for Answer Relevance, Faithfulness, Context Relevance
- ✅ No import errors or dependency conflicts

### 2. API Key Configuration
Add your IBM watsonx API key to your `.env` file:
```bash
echo "WATSONX_APIKEY=your_api_key_here" >> .env
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
- **Dependency conflicts**: Use the version pinning solution above to resolve conflicts

## Dependency Conflict Details

**The Problem**:
- `ibm-watsonx-gov[agentic]==1.2.2` tries to downgrade `openai` to `1.75.0`
- `openai-agents` requires `openai>=2.0.0` for some features
- Default dependency resolution creates conflicts

**The Solution**:
Version pinning with compatible versions:
- `openai==1.98.0` (compatible with both libraries)
- `openai-agents==0.2.5` (works with openai 1.98.0)
- `litellm==1.72.0` (compatible version)

**Why This Works**:
The pinned versions satisfy both libraries' requirements without forcing incompatible downgrades. This is a stable workaround until IBM updates `ibm-watsonx-gov` to support newer `openai` versions.

## Reference

- [IBM watsonx governance Agentic AI Evaluation SDK](https://dataplatform.cloud.ibm.com/docs/content/wsj/model/wxgov-agentic-ai-evaluation-sdk.html?context=wx&locale=en#examples)