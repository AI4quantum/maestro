#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""
Automatic evaluation middleware for Maestro agents using IBM Watsonx Governance.

This module provides transparent evaluation of agent responses using watsonx evaluation metrics
such as answer relevance, faithfulness, context relevance, etc.

Usage:
    Set MAESTRO_AUTO_EVALUATION=true to enable automatic evaluation.
    Requires WATSONX_APIKEY environment variable for actual evaluations.

Status:
    ✅ Middleware integration complete and functional
    ✅ Watsonx decorator pattern implemented correctly
    ✅ Authentication integration working
    ⏳ Pending: WATSONX_APIKEY for actual metric calculations

TODO:
    - [ ] Add database storage for evaluation results (Phase 2)
    - [ ] Implement additional metrics (content safety, readability, etc.)
    - [ ] Add configuration for metric selection
    - [ ] Add error retry logic for API failures
    - [ ] Add offline evaluation mode for development
"""

import os
import time
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not available, continue without it

# Try to import watsonx evaluation - graceful failure if not available
try:
    from ibm_watsonx_gov.evaluators.agentic_evaluator import AgenticEvaluator
    from ibm_watsonx_gov.entities.state import EvaluationState
    from ibm_watsonx_gov.entities.agentic_app import AgenticApp, MetricsConfiguration
    from ibm_watsonx_gov.metrics import (
        AnswerRelevanceMetric,
        FaithfulnessMetric,
        ContextRelevanceMetric,
        AnswerSimilarityMetric,
    )

    WATSONX_AVAILABLE = True

    class EvaluationState(EvaluationState):
        """Simple evaluation state for middleware."""

        pass

except ImportError:
    WATSONX_AVAILABLE = False

    # Define dummy classes when watsonx not available
    class EvaluationState:
        pass

    AgenticEvaluator = None
    AgenticApp = None
    MetricsConfiguration = None
    AnswerRelevanceMetric = None
    FaithfulnessMetric = None
    ContextRelevanceMetric = None
    AnswerSimilarityMetric = None


class SimpleEvaluationMiddleware:
    """
    Simple evaluation middleware that automatically evaluates agent responses.
    Designed to be lightweight and non-intrusive.
    """

    def __init__(self):
        self.evaluator = None
        self.metrics_config = None

        # Initialize evaluator if watsonx is available (we'll check enabled status at runtime)
        if WATSONX_AVAILABLE:
            self._initialize_evaluator()

    def _is_evaluation_enabled(self) -> bool:
        """Check if evaluation is enabled via environment variable."""
        return os.getenv("MAESTRO_AUTO_EVALUATION", "false").lower() == "true"

    def _initialize_evaluator(self) -> None:
        """Initialize the watsonx evaluator with basic metrics."""
        try:
            # Use comprehensive watsonx metrics
            self.metrics_config = MetricsConfiguration(
                metrics=[
                    AnswerRelevanceMetric(),
                    FaithfulnessMetric(),
                    ContextRelevanceMetric(),
                    AnswerSimilarityMetric(),
                ]
            )

            agentic_app = AgenticApp(
                name="Maestro Auto Evaluation",
                metrics_configuration=self.metrics_config,
            )

            self.evaluator = AgenticEvaluator(agentic_app=agentic_app)
            print("✅ Maestro Auto Evaluation: Watsonx evaluator initialized")

        except Exception as e:
            print(f"⚠️  Maestro Auto Evaluation: Failed to initialize evaluator: {e}")
            self.enabled = False

    async def evaluate_response(
        self, agent_name: str, prompt: str, response: str, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate an agent response and return the evaluation results.

        Args:
            agent_name: Name of the agent that generated the response
            prompt: The input prompt
            response: The agent's response
            **kwargs: Additional context (context, step_index, etc.)

        Returns:
            Dict with evaluation results or None if evaluation disabled/failed
        """

        if not self._is_evaluation_enabled():
            return None

        if not WATSONX_AVAILABLE:
            print("⚠️  Maestro Auto Evaluation: Watsonx library not available")
            return None

        if not self.evaluator:
            print("⚠️  Maestro Auto Evaluation: Evaluator not initialized")
            return None

        try:
            start_time = time.time()

            # Convert response to string if needed
            response_text = str(response) if not isinstance(response, str) else response

            print(f"🔍 Maestro Auto Evaluation: Evaluating response from {agent_name}")
            print(f"🔍 DEBUG: Context received: {kwargs.get('context', 'None')}")
            print(
                f"🔍 DEBUG: Prompt length: {len(prompt)}, Response length: {len(response_text)}"
            )

            # Start evaluation run
            self.evaluator.start_run()

            # Create evaluation input
            eval_input = {
                "input_text": prompt,
                "output": response_text,
                "interaction_id": f"maestro_{agent_name}_{int(time.time())}",
            }

            # Add context if available
            if "context" in kwargs and kwargs["context"]:
                eval_input["context"] = kwargs["context"]
            try:
                print(
                    "🔄 Maestro Auto Evaluation: Running watsonx evaluation metrics..."
                )

                # Use the correct watsonx pattern: state-based evaluation
                evaluation_results = {}

                try:
                    print(
                        "🔍 DEBUG: Using correct watsonx state-based evaluation pattern..."
                    )

                    # Create the state object that will be mutated by the decorated functions
                    state = EvaluationState(
                        input_text=prompt, interaction_id=eval_input["interaction_id"]
                    )

                    # Populate context if available
                    if "context" in eval_input and eval_input["context"]:
                        state.context = [
                            eval_input["context"]
                        ]  # Context should be a list

                    # Apply decorator and trigger evaluation
                    # The function must update the state object as a side effect
                    @self.evaluator.evaluate_answer_relevance
                    def run_answer_relevance(state: EvaluationState, config=None):
                        """Function that mutates state object for answer relevance evaluation."""
                        state.generated_text = response_text
                        # Return a dictionary as expected by the watsonx library
                        return {
                            "generated_text": response_text,
                            "input_text": state.input_text,
                            "interaction_id": state.interaction_id,
                            "context": state.context
                            if hasattr(state, "context")
                            else [],
                        }

                    run_answer_relevance(state, None)
                    print("✅ Triggered answer relevance evaluation.")
                    evaluation_results["answer_relevance"] = "triggered"

                except Exception as relevance_error:
                    print(f"⚠️  Answer relevance evaluation failed: {relevance_error}")
                    print(
                        f"🔍 DEBUG: Full error details: {type(relevance_error).__name__}: {str(relevance_error)}"
                    )
                    import traceback

                    print("🔍 DEBUG: Full traceback:")
                    traceback.print_exc()
                    evaluation_results["answer_relevance"] = None

                # Faithfulness - use state-based evaluation
                try:
                    # Faithfulness typically requires context, so only run if we have it
                    if "context" in eval_input and eval_input["context"]:
                        print(
                            "🔍 DEBUG: Using state-based evaluation for faithfulness..."
                        )

                        @self.evaluator.evaluate_faithfulness
                        def run_faithfulness(state: EvaluationState, config=None):
                            """Function that mutates state object for faithfulness evaluation."""
                            state.generated_text = response_text
                            state.context = (
                                state.context
                            )  # Re-assign to ensure it's present
                            # Return a dictionary as expected by the watsonx library
                            return {
                                "generated_text": response_text,
                                "input_text": state.input_text,
                                "interaction_id": state.interaction_id,
                                "context": state.context
                                if hasattr(state, "context")
                                else [],
                            }

                        run_faithfulness(state, None)
                        print("✅ Triggered faithfulness evaluation.")
                        evaluation_results["faithfulness"] = "triggered"
                    else:
                        print(
                            "ℹ️  Skipping faithfulness evaluation (no context provided)"
                        )
                except Exception as faithfulness_error:
                    print(f"⚠️  Faithfulness evaluation failed: {faithfulness_error}")
                    print(
                        f"🔍 DEBUG: Full error details: {type(faithfulness_error).__name__}: {str(faithfulness_error)}"
                    )
                    evaluation_results["faithfulness"] = None

                # Context Relevance - use state-based evaluation
                try:
                    if "context" in eval_input and eval_input["context"]:
                        print(
                            "🔍 DEBUG: Using state-based evaluation for context relevance..."
                        )

                        @self.evaluator.evaluate_context_relevance
                        def run_context_relevance(state: EvaluationState, config=None):
                            """Function that mutates state object for context relevance evaluation."""
                            state.generated_text = response_text
                            state.context = (
                                state.context
                            )  # Re-assign to ensure it's present
                            # Return a dictionary as expected by the watsonx library
                            return {
                                "generated_text": response_text,
                                "input_text": state.input_text,
                                "interaction_id": state.interaction_id,
                                "context": state.context
                                if hasattr(state, "context")
                                else [],
                            }

                        run_context_relevance(state, None)
                        print("✅ Triggered context relevance evaluation.")
                        evaluation_results["context_relevance"] = "triggered"
                    else:
                        print(
                            "ℹ️  Skipping context relevance evaluation (no context provided)"
                        )
                except Exception as context_relevance_error:
                    print(
                        f"⚠️  Context relevance evaluation failed: {context_relevance_error}"
                    )
                    print(
                        f"🔍 DEBUG: Full error details: {type(context_relevance_error).__name__}: {str(context_relevance_error)}"
                    )
                    evaluation_results["context_relevance"] = None

                # Answer Similarity - measures similarity between expected and actual answers
                try:
                    # Note: This metric typically requires an expected/reference answer
                    # For now, we'll skip it unless we have a reference answer in context
                    if "expected_answer" in kwargs and kwargs["expected_answer"]:

                        @self.evaluator.evaluate_answer_similarity
                        def run_answer_similarity(state: EvaluationState, config=None):
                            """Function that mutates state object for answer similarity evaluation."""
                            state.generated_text = response_text
                            state.expected_answer = kwargs["expected_answer"]
                            # Return a dictionary as expected by the watsonx library
                            return {
                                "generated_text": response_text,
                                "input_text": state.input_text,
                                "interaction_id": state.interaction_id,
                                "expected_answer": kwargs["expected_answer"],
                            }

                        run_answer_similarity(state, None)
                        print("✅ Triggered answer similarity evaluation.")
                        evaluation_results["answer_similarity"] = "triggered"
                    else:
                        print(
                            "ℹ️  Skipping answer similarity evaluation (no expected answer provided)"
                        )
                except Exception as answer_similarity_error:
                    print(
                        f"⚠️  Answer similarity evaluation failed: {answer_similarity_error}"
                    )

                print(
                    f"📊 Maestro Auto Evaluation: Completed {len(evaluation_results)} metrics"
                )

            except Exception as eval_error:
                print(
                    f"⚠️  Maestro Auto Evaluation: Evaluation call failed: {eval_error}"
                )
                evaluation_results = {}

            # Capture results from __online_metric_results BEFORE end_run()
            # This is where the actual metric scores are stored
            online_results = getattr(
                self.evaluator, "_AgenticEvaluator__online_metric_results", []
            )
            print(
                f"🔍 DEBUG: Found {len(online_results)} online metric results before end_run()"
            )

            # Extract the actual metric scores
            for i, metric_result in enumerate(online_results):
                print(f"🔍 DEBUG: Online metric result {i}: {metric_result}")
                print(f"🔍 DEBUG: Metric name: {metric_result.name}")
                print(f"🔍 DEBUG: Metric value: {metric_result.value}")
                print(f"🔍 DEBUG: Metric method: {metric_result.method}")
                print(f"🔍 DEBUG: Metric provider: {metric_result.provider}")

                # Store the actual scores
                if metric_result.name in [
                    "answer_relevance",
                    "faithfulness",
                    "context_relevance",
                    "answer_similarity",
                ]:
                    evaluation_results[f"{metric_result.name}_score"] = (
                        metric_result.value
                    )
                    evaluation_results[f"{metric_result.name}_method"] = (
                        metric_result.method
                    )
                    evaluation_results[f"{metric_result.name}_provider"] = (
                        metric_result.provider
                    )
                    print(f"✅ Found {metric_result.name} score: {metric_result.value}")

            self.evaluator.end_run()
            eval_result = self.evaluator.get_result()

            # DEBUG: Let's examine the evaluator result to find the actual scores
            print(f"🔍 DEBUG: Evaluator result type: {type(eval_result)}")
            print(f"🔍 DEBUG: Evaluator result: {eval_result}")

            # Check if we have any metrics results in the evaluator result
            if hasattr(eval_result, "metrics_results") and eval_result.metrics_results:
                print(
                    f"🔍 DEBUG: Found {len(eval_result.metrics_results)} metrics results!"
                )
                for i, metric_result in enumerate(eval_result.metrics_results):
                    print(f"🔍 DEBUG: Metric result {i}: {metric_result}")
                    print(f"🔍 DEBUG: Metric name: {metric_result.name}")
                    print(f"🔍 DEBUG: Metric value: {metric_result.value}")
                    print(f"🔍 DEBUG: Metric node_name: {metric_result.node_name}")
            else:
                print("🔍 DEBUG: No metrics results found in evaluator result")

            # Now that all decorated functions have been called, get the aggregated results
            print("🔍 DEBUG: Getting aggregated evaluation results...")

            # Check if we have any metrics results in the evaluator result
            if hasattr(eval_result, "metrics_results") and eval_result.metrics_results:
                print(
                    f"🔍 DEBUG: Found {len(eval_result.metrics_results)} metrics results!"
                )
                for i, metric_result in enumerate(eval_result.metrics_results):
                    print(f"🔍 DEBUG: Metric result {i}: {metric_result}")
                    print(f"🔍 DEBUG: Metric name: {metric_result.name}")
                    print(f"🔍 DEBUG: Metric value: {metric_result.value}")
                    print(f"🔍 DEBUG: Metric node_name: {metric_result.node_name}")

                    # Store the actual scores
                    if metric_result.name in [
                        "answer_relevance",
                        "faithfulness",
                        "context_relevance",
                        "answer_similarity",
                    ]:
                        evaluation_results[f"{metric_result.name}_score"] = (
                            metric_result.value
                        )
                        print(
                            f"✅ Found {metric_result.name} score: {metric_result.value}"
                        )
            else:
                print("🔍 DEBUG: No metrics results found in evaluator result")

            # Try to get individual metric results by node name
            try:
                print(
                    "🔍 DEBUG: Trying to get individual metric results by node name..."
                )
                for metric_name in [
                    "answer_relevance",
                    "faithfulness",
                    "context_relevance",
                ]:
                    try:
                        # Try different node names that might have been used
                        for node_name in [
                            "mock_agent_response",
                            "mock_agent_response_faithfulness",
                            "mock_agent_response_context_relevance",
                        ]:
                            try:
                                metric_result = self.evaluator.get_metric_result(
                                    metric_name, node_name
                                )
                                print(
                                    f"🔍 DEBUG: {metric_name} result for {node_name}: {metric_result}"
                                )
                                if metric_result:
                                    evaluation_results[f"{metric_name}_score"] = (
                                        metric_result
                                    )
                            except Exception as node_error:
                                print(
                                    f"🔍 DEBUG: {metric_name} for {node_name} failed: {node_error}"
                                )
                                continue
                    except Exception as metric_error:
                        print(f"🔍 DEBUG: {metric_name} error: {metric_error}")
            except Exception as individual_error:
                print(
                    f"🔍 DEBUG: Individual metric retrieval failed: {individual_error}"
                )

            try:
                df = eval_result.to_df()
                print(f"🔍 DEBUG: DataFrame shape: {df.shape}")
                print(f"🔍 DEBUG: DataFrame columns: {list(df.columns)}")
                print(f"🔍 DEBUG: DataFrame head:\n{df.head()}")
                evaluation_data = self._extract_evaluation_data(df)
            except Exception as df_error:
                print(
                    f"📊 Maestro Auto Evaluation: DataFrame conversion issue: {df_error}"
                )

                # Try to get individual metric results
                try:
                    print("🔍 DEBUG: Trying to get individual metric results...")
                    for metric_name in [
                        "answer_relevance",
                        "faithfulness",
                        "context_relevance",
                        "answer_similarity",
                    ]:
                        try:
                            metric_result = self.evaluator.get_metric_result(
                                metric_name
                            )
                            print(f"🔍 DEBUG: {metric_name} result: {metric_result}")
                        except Exception as metric_error:
                            print(f"🔍 DEBUG: {metric_name} error: {metric_error}")
                except Exception as metric_error:
                    print(
                        f"🔍 DEBUG: Individual metric retrieval failed: {metric_error}"
                    )

                evaluation_data = {
                    "status": "evaluator_ready",
                    "note": "Evaluation framework initialized but no metrics calculated yet",
                    "framework": "watsonx_governance",
                }

            end_time = time.time()
            evaluation_time = end_time - start_time

            # Create final result with actual metric scores
            final_result = {
                "agent_name": agent_name,
                "prompt": prompt,
                "response": response_text,
                "evaluation_time_ms": int(evaluation_time * 1000),
                "timestamp": int(time.time()),
                "evaluator": "watsonx_governance",
                "metrics": evaluation_data,
                "watsonx_scores": {
                    key: value
                    for key, value in evaluation_results.items()
                    if key.endswith("_score")
                },
                "watsonx_methods": {
                    key: value
                    for key, value in evaluation_results.items()
                    if key.endswith("_method")
                },
                "watsonx_providers": {
                    key: value
                    for key, value in evaluation_results.items()
                    if key.endswith("_provider")
                },
            }

            # Print the evaluation structure (for POC visibility)
            self._print_evaluation_summary(final_result)

            return final_result

        except Exception as e:
            print(f"❌ Maestro Auto Evaluation: Evaluation failed: {e}")
            return {
                "agent_name": agent_name,
                "error": str(e),
                "status": "evaluation_failed",
            }

    def _extract_evaluation_data(self, df) -> Dict[str, Any]:
        """Extract evaluation data from watsonx DataFrame."""
        if df.empty:
            return {"status": "no_data", "note": "No evaluation metrics available"}

        # Extract the first row as evaluation results
        row = df.iloc[0]
        metrics = {}

        # Extract known metric columns
        for col in df.columns:
            if col.startswith(
                (
                    "answer_relevance",
                    "faithfulness",
                    "context_relevance",
                    "answer_similarity",
                    "hap",
                    "pii",
                    "harm",
                )
            ):
                metrics[col] = row[col]

        return {
            "status": "success",
            "dataframe_shape": df.shape,
            "dataframe_columns": list(df.columns),
            "metrics": metrics,
        }

    def _print_evaluation_summary(self, result: Dict[str, Any]) -> None:
        """Print a concise evaluation summary."""
        agent_name = result.get("agent_name", "unknown")
        eval_time = result.get("evaluation_time_ms", 0)

        print(f"📊 Maestro Auto Evaluation Summary for {agent_name}:")
        print(f"   ⏱️  Evaluation time: {eval_time}ms")

        metrics = result.get("metrics", {})
        if isinstance(metrics, dict):
            if "status" in metrics:
                print(f"   📈 Status: {metrics['status']}")
                if "note" in metrics:
                    print(f"   📝 Note: {metrics['note']}")

            # Print any actual metric values
            metric_values = metrics.get("metrics", {}) if "metrics" in metrics else {}
            if metric_values:
                print(f"   📏 Metrics calculated: {len(metric_values)}")
                for key, value in metric_values.items():
                    print(f"      {key}: {value}")

        # Show actual watsonx scores if available
        if "watsonx_scores" in result and result["watsonx_scores"]:
            print("   🎯 Watsonx Evaluation Scores:")
            for metric_name, score in result["watsonx_scores"].items():
                method = result.get("watsonx_methods", {}).get(
                    f"{metric_name.replace('_score', '')}_method", "unknown"
                )
                provider = result.get("watsonx_providers", {}).get(
                    f"{metric_name.replace('_score', '')}_provider", "unknown"
                )
                print(f"      {metric_name}: {score:.3f} ({method} via {provider})")
        else:
            # Show the structure that would go to database
            print("   🗄️  Database structure preview:")
            print(f"      agent_name: {result.get('agent_name')}")
            print(f"      timestamp: {result.get('timestamp')}")
            print(f"      prompt_length: {len(result.get('prompt', ''))}")
            print(f"      response_length: {len(result.get('response', ''))}")
            print(f"      evaluator: {result.get('evaluator')}")


# Global middleware instance
_evaluation_middleware = None


def get_evaluation_middleware() -> SimpleEvaluationMiddleware:
    """Get the global evaluation middleware instance."""
    global _evaluation_middleware
    if _evaluation_middleware is None:
        _evaluation_middleware = SimpleEvaluationMiddleware()
    return _evaluation_middleware


async def auto_evaluate_response(
    agent_name: str, prompt: str, response: str, **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Convenience function for automatic response evaluation.

    This is the main function that agents will call to evaluate their responses.
    """
    middleware = get_evaluation_middleware()
    return await middleware.evaluate_response(agent_name, prompt, response, **kwargs)
