# Watsonx Evaluation Integration for Maestro

## Overview

This document outlines the integration of IBM's watsonx governance evaluation capabilities into the Maestro multi-agent platform. The goal is to automatically evaluate agent responses for quality, safety, and reliability.

We have successfully implemented **automatic evaluation middleware** that seamlessly integrates with existing Maestro agents without requiring any code changes. **The system is fully functional and returning actual metric scores!**

### ✅ What's Working

#### 1. **Automatic Evaluation Middleware**
- **Zero Configuration**: Just set `MAESTRO_AUTO_EVALUATION=true` to enable
- **Transparent Integration**: Works with any existing agent (`MockAgent`, `OpenAIAgent`, etc.)
- **Production Ready**: Graceful fallback when watsonx library isn't available
- **Clean Implementation**: Minimal debug output, production-ready code
- **Real Metrics**: Returns actual numerical scores from watsonx evaluation

#### 2. **Watsonx Integration**
- **Decorator Pattern**: Successfully implemented IBM watsonx's decorator-based evaluation
- **Authentication**: Integrated with IBM Cloud API authentication
- **Multiple Metrics**: Evaluates:
  - **Answer Relevance**: Measures how well the response addresses the question
  - **Faithfulness**: Measures how faithful the response is to provided context
  - **Context Relevance**: Measures how relevant the context is to the question
  - **Answer Similarity**: Measures similarity between expected and actual answers
- **Actual Scores**: Returns real numerical scores (0.0-1.0) with evaluation methods

#### 2.1. **Available Metrics (Current)**

| Metric              | Needs Context? | Needs Expected Answer? | Notes |
|---------------------|----------------|-------------------------|-------|
| Answer Relevance    | No             | No                      | Response addresses the question |
| Faithfulness        | Yes            | No                      | Response grounded in provided context |
| Context Relevance   | Yes            | No                      | Context relevance to the question |
| Answer Similarity   | No             | Yes                     | Similarity to a reference answer |

Inputs:
- Context must be a list of strings (e.g., `["doc chunk 1", "doc chunk 2"]`).
- Expected answer is a single string.
- If a required input is missing, that metric is skipped gracefully.

#### 3. **Environment Setup**
- **Python 3.11**: Dedicated `.venv-eval` environment for watsonx compatibility
- **Dual Environment**: Separate evaluation environment from main development
- **Error Handling**: Robust error handling for missing dependencies
- **Environment Variables**: Proper integration with `WATSONX_APIKEY` requirement

### 🔧 Current Implementation

#### Core Files
```
src/maestro/agents/evaluation_middleware.py   # Main evaluation middleware
src/maestro/agents/mock_agent.py             # Updated with middleware integration
tests/yamls/agents/evaluation_test_agent.yaml      # Test agent configuration
tests/yamls/workflows/evaluation_test_workflow.yaml # Test workflow
```

#### How It Works
1. **Agent runs normally** → generates response
2. **Middleware automatically activates** (if `MAESTRO_AUTO_EVALUATION=true`)
3. **Watsonx evaluation decorators applied** → calculates metrics
4. **Results logged** → ready for database storage (Phase 2)

### 📊 Evaluation Flow

```mermaid
graph LR
    A[Agent.run()] --> B[Generate Response]
    B --> C{Auto Eval Enabled?}
    C -->|Yes| D[Create Watsonx Decorator]
    D --> E[Run Evaluation Metrics]
    E --> F[Log Results]
    F --> G[Return Response]
    C -->|No| G
```

### ⚡ Performance
- **Evaluation Time**: typically ~3–6 seconds per evaluation (varies by metrics and provider)
- **Async Compatible**: Non-blocking integration
- **Error Resilient**: Never breaks agent execution
- **Real Scores**: Actual numerical metrics (0.0-1.0 scale)

## Current Status & Next Steps

### ✅ **Production Ready - Fully Functional**
- **Status**: All code integration complete and tested with real metrics
- **Verification**: Successfully returning actual watsonx evaluation scores
- **Environment**: Python 3.11 evaluation environment working perfectly
- **Metrics**: Answer Relevance, Faithfulness, Context Relevance all functional

### 🚀 **Phase 2: Database Integration** (Future)
- [ ] Design database schema for evaluation results
- [ ] Add persistent storage for metrics
- [ ] Create analytics dashboard
- [ ] Add metric aggregation and reporting

### 🎯 **Phase 3: Advanced Features** (Future)
- [ ] Configurable metric selection
- [ ] Real-time evaluation monitoring
- [ ] Custom evaluation rules
- [ ] Integration with other evaluation libraries

### ⚙️ **Configuration**
- Current:
  - `MAESTRO_AUTO_EVALUATION=true` enables evaluation globally.
- Planned:
  - `MAESTRO_EVAL_METRICS` to select metrics, e.g. `answer_relevance,faithfulness,context_relevance`.

## Usage Instructions

### 🚀 **Quick Start (Recommended)**

1. **Activate the evaluation environment**:
   ```bash
   source .venv-eval/bin/activate
   ```

2. **Enable automatic evaluation**:
   ```bash
   export MAESTRO_AUTO_EVALUATION=true
   ```

3. **Run any workflow** - evaluation happens automatically:
   ```bash
   # Test with mock agent
   maestro run tests/yamls/agents/evaluation_test_agent.yaml tests/yamls/workflows/evaluation_test_workflow.yaml
   
   # Test with OpenAI agent
   maestro run tests/yamls/agents/openai_agent.yaml tests/yamls/workflows/openai_workflow.yaml
   ```

### 🔧 **Environment Setup**

The evaluation system uses a dedicated Python 3.11 environment:

```bash
# Create evaluation environment (already done)
python3.11 -m venv .venv-eval

# Activate evaluation environment
source .venv-eval/bin/activate

# Install dependencies (already done)
pip install "ibm-watsonx-gov[agentic]"
pip install -e .
```

Note: watsonx requires Python 3.11. Keep evaluation in `.venv-eval` while core Maestro may run on 3.12+.

### 📊 **Expected Output**

When evaluation is enabled, you'll see output like:

```bash
✅ Maestro Auto Evaluation: Watsonx evaluator initialized
🔍 Maestro Auto Evaluation: Evaluating response from my-agent
📊 Maestro Auto Evaluation: Completed N metrics
📊 Maestro Auto Evaluation Summary for my-agent:
   ⏱️  Evaluation time: ~3–6s
   📈 Status: evaluator_ready
   🎯 Watsonx Evaluation Scores:
      answer_relevance_score: 0.28x (token_recall via unitxt)
      faithfulness_score: 0.40x (token_k_precision via unitxt)
      context_relevance_score: 0.55x (token_precision via unitxt)
```

### Environment Variables
- `MAESTRO_AUTO_EVALUATION=true` - Enable automatic evaluation
- `WATSONX_APIKEY=<key>` - IBM watsonx API key for actual evaluations

## Real Test Results

### MockAgent Test Results
```bash
📊 Maestro Auto Evaluation Summary for evaluation-test-agent:
   ⏱️  Evaluation time: 5508ms
   📈 Status: evaluator_ready
   🎯 Watsonx Evaluation Scores:
      answer_relevance_score: 0.556 (token_recall via unitxt)
      faithfulness_score: 0.409 (token_k_precision via unitxt)
      context_relevance_score: 0.556 (token_precision via unitxt)
```

### OpenAI Agent Test Results
```bash
📊 Maestro Auto Evaluation Summary for my-agent:
   ⏱️  Evaluation time: 3502ms
   📈 Status: evaluator_ready
   🎯 Watsonx Evaluation Scores:
      answer_relevance_score: 0.286 (token_recall via unitxt)
```

**Note**: Context-based metrics (faithfulness, context_relevance) are skipped when no context is provided, which is expected behavior.

### 🧩 Extending Metrics
Additional metrics (e.g., content safety, readability, retrieval quality) can be added with minimal code:

```python
# Inside evaluation_middleware.py metrics configuration
self.metrics_config = MetricsConfiguration(metrics=[
    AnswerRelevanceMetric(),
    FaithfulnessMetric(),
    ContextRelevanceMetric(),
    AnswerSimilarityMetric(),
    # Add: ContentSafetyMetric(), ReadabilityMetric(), RetrievalQualityMetric(), ...
])
```

Some metrics require more inputs (e.g., context list, references/expected answer). Adding more metrics may increase latency.

### 🛠️ Troubleshooting
- Empty or missing scores: verify `WATSONX_APIKEY` and provider access; ensure required inputs present.
- Skipped metrics: provide `context` (list[str]) or `expected_answer` (str) as needed.
- DataFrame conversion warnings: occur when no tabular result is available; not fatal.
- Instrumentation warnings (e.g., fastapi/generativeai): safe to ignore unless using those providers.

## Architecture

The evaluation middleware follows a **decorator pattern** that wraps agent responses:

1. **Minimal Integration**: No changes needed to existing agents
2. **Configurable Activation**: Environment variable controls enable/disable
3. **Extensible Design**: Easy to add new metrics and evaluation providers
4. **Error Resilient**: Never impacts core agent functionality

## Conclusion

The watsonx evaluation integration is **production-ready and fully functional** with:
- ✅ Seamless integration with existing Maestro agents
- ✅ Automatic evaluation without code changes
- ✅ Proper watsonx library integration with Python 3.11
- ✅ Real metric scores being returned (Answer Relevance, Faithfulness, Context Relevance)
- ✅ Dedicated evaluation environment (`.venv-eval`) for compatibility
- ✅ **Ready for production use** - just activate the evaluation environment!

### 🎯 **Current Capabilities**
- **Answer Relevance**: Measures how well responses address questions (0.0-1.0 scale)
- **Faithfulness**: Measures how faithful responses are to provided context
- **Context Relevance**: Measures how relevant context is to questions
- **Answer Similarity**: Measures similarity between expected and actual answers
- **Performance**: ~3-6 seconds per evaluation (LLM-based metrics)

This provides a solid foundation for comprehensive agent evaluation and monitoring in production environments. The system is ready for immediate use and future database integration.