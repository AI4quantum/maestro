# Scoring Agent

The Scoring Agent is a specialized agent in Maestro that uses Opik to evaluate the quality of responses from other agents. It provides metrics like relevance and hallucination detection to help assess the quality of AI-generated content.

## Setup

### 1. Get Your COMET API Key

1. Visit the [Opik Dashboard](https://www.comet.com/opik/) online
2. Sign up or log in to your account
3. Navigate to your API keys section
4. Copy your `COMET_API_KEY`

### 2. Configure Environment

Add your COMET API key to your `.env` file:

```bash
COMET_API_KEY=your_comet_api_key_here
```

## Defining a Scoring Agent

Create a scoring agent in your `agents.yaml` file:

```yaml
apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: score
  labels: 
    app: test-example
    custom_agent: scoring_agent
spec:
  model: qwen3
  framework: custom
  mode: remote
  description: not used
  instructions: not used
```

Note: The model you define here is actually relevant, that will be the model the scoring agent uses to evaluate.

## Integrating into Workflows

Add the scoring agent to your workflow to evaluate responses from other agents, define it as you would for any other agent:

```yaml
agents:
    - simple_test
    - score
prompt: Is the most well known "Paris" the city in the United States?
steps:
    - name: answer
    agent: simple_test
    - name: scoring
    agent: score
    from: [prompt, answer]        # → run's first arg = original prompt, second arg = answer's reply
    outputs:
        - answer               # → re-emit the raw response downstream (so that it theres an agent after, we still have the output of the previous non-score agent) 
```

## Output

The scoring agent will return evaluation metrics that include:
- **Relevance Score**: How well the response answers the question (0-1)
- **Hallucination Score**: Likelihood of false information (0-1)
- **Overall Quality Assessment**: Summary of the evaluation

## Token Usage

Unlike traditional LLM agents, the scoring agent doesn't consume traditional prompt/response tokens. Instead, it uses Opik's evaluation framework and will show as a custom agent type in token usage summaries.

## Notes

- The scoring agent requires a valid `COMET_API_KEY` to function
- It's designed to work with any text response from other agents
- The evaluation metrics are provided by Opik's advanced evaluation models
- You can customize the evaluation prompt to focus on specific aspects of response quality
