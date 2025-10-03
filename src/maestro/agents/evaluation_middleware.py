#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""
Automatic evaluation middleware for Maestro agents using IBM Watsonx Governance.

This module provides transparent evaluation of agent responses using watsonx evaluation metrics
such as answer relevance, faithfulness, context relevance, etc.

Usage:
    Set MAESTRO_AUTO_EVALUATION=true to enable automatic evaluation.
    Requires WATSONX_APIKEY environment variable for actual evaluations.
"""

import os
import time
from typing import Dict, Any, Optional
import pandas as pd

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    raise ImportError(
        "Missing required dependency: python-dotenv. "
        "Install it with: pip install python-dotenv or uv pip install python-dotenv. "
        "This is required for loading environment variables including WATSONX_APIKEY."
    )

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
            # TODO(maestro-eval): Extend metrics beyond core QA set.
            # - Candidates:
            #   - Content Safety (toxicity/PII/harm)
            #   - Readability/Fluency
            #   - Retrieval Quality variants (groundedness/coverage/support)
            # - Notes:
            #   - Some metrics require additional inputs (e.g., context list, references,
            #     expected_answer). Ensure the state is populated accordingly.
            #   - Adding more metrics may increase evaluation latency.
            #   - Make metric selection configurable via env (e.g., MAESTRO_EVAL_METRICS).
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

                evaluation_results = {}

                try:
                    state = EvaluationState(
                        input_text=prompt, interaction_id=eval_input["interaction_id"]
                    )

                    if "context" in eval_input and eval_input["context"]:
                        state.context = [eval_input["context"]]

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
                    evaluation_results["answer_relevance"] = "triggered"

                except Exception as relevance_error:
                    print(f"⚠️  Answer relevance evaluation failed: {relevance_error}")
                    evaluation_results["answer_relevance"] = None

                try:
                    if "context" in eval_input and eval_input["context"]:

                        @self.evaluator.evaluate_faithfulness
                        def run_faithfulness(state: EvaluationState, config=None):
                            """Function that mutates state object for faithfulness evaluation."""
                            state.generated_text = response_text
                            state.context = state.context
                            return {
                                "generated_text": response_text,
                                "input_text": state.input_text,
                                "interaction_id": state.interaction_id,
                                "context": state.context
                                if hasattr(state, "context")
                                else [],
                            }

                        run_faithfulness(state, None)
                        evaluation_results["faithfulness"] = "triggered"
                    else:
                        print(
                            "ℹ️  Skipping faithfulness evaluation (no context provided)"
                        )
                except Exception as faithfulness_error:
                    print(f"⚠️  Faithfulness evaluation failed: {faithfulness_error}")
                    evaluation_results["faithfulness"] = None

                try:
                    if "context" in eval_input and eval_input["context"]:

                        @self.evaluator.evaluate_context_relevance
                        def run_context_relevance(state: EvaluationState, config=None):
                            """Function that mutates state object for context relevance evaluation."""
                            state.generated_text = response_text
                            state.context = state.context
                            return {
                                "generated_text": response_text,
                                "input_text": state.input_text,
                                "interaction_id": state.interaction_id,
                                "context": state.context
                                if hasattr(state, "context")
                                else [],
                            }

                        run_context_relevance(state, None)
                        evaluation_results["context_relevance"] = "triggered"
                    else:
                        print(
                            "ℹ️  Skipping context relevance evaluation (no context provided)"
                        )
                except Exception as context_relevance_error:
                    print(
                        f"⚠️  Context relevance evaluation failed: {context_relevance_error}"
                    )
                    evaluation_results["context_relevance"] = None

                try:
                    if "expected_answer" in kwargs and kwargs["expected_answer"]:

                        @self.evaluator.evaluate_answer_similarity
                        def run_answer_similarity(state: EvaluationState, config=None):
                            """Function that mutates state object for answer similarity evaluation."""
                            state.generated_text = response_text
                            state.expected_answer = kwargs["expected_answer"]
                            return {
                                "generated_text": response_text,
                                "input_text": state.input_text,
                                "interaction_id": state.interaction_id,
                                "expected_answer": kwargs["expected_answer"],
                            }

                        run_answer_similarity(state, None)
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
            online_results = getattr(
                self.evaluator, "_AgenticEvaluator__online_metric_results", []
            )

            for metric_result in online_results:
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

            self.evaluator.end_run()
            eval_result = self.evaluator.get_result()

            # Check if we have any metrics results in the evaluator result
            if hasattr(eval_result, "metrics_results") and eval_result.metrics_results:
                for metric_result in eval_result.metrics_results:
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

            if evaluation_results:
                try:
                    df = self._create_evaluation_dataframe(
                        evaluation_results, eval_input["interaction_id"]
                    )
                    evaluation_data = self._extract_evaluation_data(df)
                except Exception as df_error:
                    print(
                        f"📊 Maestro Auto Evaluation: DataFrame creation issue: {df_error}"
                    )
                    evaluation_data = {
                        "status": "dataframe_creation_failed",
                        "note": "Failed to create DataFrame from captured results",
                        "framework": "watsonx_governance",
                        "metrics_count": len(
                            [
                                k
                                for k in evaluation_results.keys()
                                if k.endswith("_score")
                            ]
                        ),
                    }
            else:
                evaluation_data = {
                    "status": "no_metrics",
                    "note": "No evaluation metrics were captured",
                    "framework": "watsonx_governance",
                }

            end_time = time.time()
            evaluation_time = end_time - start_time

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

            self._print_evaluation_summary(final_result)

            return final_result

        except Exception as e:
            print(f"❌ Maestro Auto Evaluation: Evaluation failed: {e}")
            return {
                "agent_name": agent_name,
                "error": str(e),
                "status": "evaluation_failed",
            }

    def _create_evaluation_dataframe(
        self, evaluation_results: Dict[str, Any], interaction_id: str
    ) -> pd.DataFrame:
        """Create a DataFrame from captured evaluation results.

        This works around the watsonx library bug where to_df() fails.
        """

        df_data = []
        for metric_name, score in evaluation_results.items():
            if metric_name.endswith("_score"):
                base_name = metric_name.replace("_score", "")
                method = evaluation_results.get(f"{base_name}_method", "unknown")
                provider = evaluation_results.get(f"{base_name}_provider", "unknown")

                df_data.append(
                    {
                        "interaction_id": interaction_id,
                        "metric_name": base_name,
                        "value": score,
                        "method": method,
                        "provider": provider,
                        "applies_to": "interaction",
                        "node_name": "evaluation",
                    }
                )

        if df_data:
            df = pd.DataFrame(df_data)

            def col_name(row):
                if row["applies_to"] == "node":
                    return f"{row['node_name']}.{row['metric_name']}"
                elif row["applies_to"] == "interaction":
                    return f"interaction.{row['metric_name']}"
                else:
                    return f"unknown.{row['metric_name']}"

            df["idx"] = df.apply(col_name, axis=1)
            df_wide = (
                df.pivot_table(index="interaction_id", columns="idx", values="value")
                .reset_index()
                .rename_axis("", axis=1)
            )

            return df_wide
        else:
            return pd.DataFrame()

    def _extract_evaluation_data(self, df) -> Dict[str, Any]:
        """Extract evaluation data from watsonx DataFrame."""
        if df.empty:
            return {"status": "no_data", "note": "No evaluation metrics available"}

        row = df.iloc[0]
        metrics = {}
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

            metric_values = metrics.get("metrics", {}) if "metrics" in metrics else {}
            if metric_values:
                print(f"   📏 Metrics calculated: {len(metric_values)}")
                for key, value in metric_values.items():
                    print(f"      {key}: {value}")

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
            print("   🗄️  Database structure preview:")
            print(f"      agent_name: {result.get('agent_name')}")
            print(f"      timestamp: {result.get('timestamp')}")
            print(f"      prompt_length: {len(result.get('prompt', ''))}")
            print(f"      response_length: {len(result.get('response', ''))}")
            print(f"      evaluator: {result.get('evaluator')}")


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
