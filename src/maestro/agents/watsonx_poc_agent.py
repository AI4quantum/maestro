#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""
Minimal POC for watsonx evaluation integration.
Just tests the basic library functionality and shows output structure.
"""

from typing import Dict, Any
from maestro.agents.agent import Agent

# Try to import watsonx evaluation - graceful failure if not available
try:
    from ibm_watsonx_gov.evaluators.agentic_evaluator import AgenticEvaluator
    from ibm_watsonx_gov.entities.state import EvaluationState
    from ibm_watsonx_gov.entities.agentic_app import AgenticApp, MetricsConfiguration
    from ibm_watsonx_gov.metrics import AnswerRelevanceMetric, FaithfulnessMetric

    WATSONX_AVAILABLE = True

    class AppState(EvaluationState):
        """Simple evaluation state for POC."""

        pass

except ImportError as e:
    WATSONX_AVAILABLE = False
    import_error = str(e)

    # Define dummy classes when watsonx not available
    class AppState:
        """Dummy state class when watsonx not available."""

        pass

    AgenticEvaluator = None
    AgenticApp = None
    MetricsConfiguration = None
    AnswerRelevanceMetric = None
    FaithfulnessMetric = None


class WatsonxPocAgent(Agent):
    """
    Minimal POC agent to test watsonx evaluation library output.
    No logging, no database - just shows what the library returns.
    """

    def __init__(self, agent: dict) -> None:
        super().__init__(agent)
        self.name = agent.get("name", "watsonx-poc")

        if not WATSONX_AVAILABLE:
            print(f"⚠️  Watsonx library not available: {import_error}")
            print("   Install with: pip install 'ibm-watsonx-gov[agentic]'")
            self.evaluator = None
            return

        # Initialize minimal evaluator with basic metrics
        self.evaluator = self._create_basic_evaluator()

    def _create_basic_evaluator(self) -> AgenticEvaluator:
        """Create the simplest possible evaluator for POC."""
        try:
            # Define minimal agentic app with just answer relevance
            metrics_config = MetricsConfiguration(
                metrics=[AnswerRelevanceMetric(), FaithfulnessMetric()]
            )

            agentic_app = AgenticApp(
                name="POC Evaluation", metrics_configuration=metrics_config
            )

            return AgenticEvaluator(agentic_app=agentic_app)

        except Exception as e:
            print(f"⚠️  Failed to create evaluator: {e}")
            return None

    async def run(self, prompt: str, response: str, **kwargs) -> Dict[str, Any]:
        """
        Run basic evaluation and return raw results for inspection.

        Args:
            prompt: The input prompt
            response: The response to evaluate

        Returns:
            Dict with original data + raw evaluation results
        """

        print("\n🔍 POC Evaluation Starting...")
        print(f"📝 Prompt: {prompt}")
        print(f"🤖 Response: {response}")

        if not self.evaluator:
            return {
                "prompt": prompt,
                "response": response,
                "evaluation_available": False,
                "error": "Watsonx evaluation library not available",
            }

        try:
            # Start evaluation run
            self.evaluator.start_run()

            # Create evaluation input
            eval_input = {
                "input_text": prompt,
                "output": response,
                "interaction_id": f"poc_{id(prompt)}",
            }

            # Add any additional context from kwargs
            if "context" in kwargs:
                eval_input["context"] = kwargs["context"]
            if "ground_truth" in kwargs:
                eval_input["ground_truth"] = kwargs["ground_truth"]

            print(f"📊 Evaluation input: {eval_input}")

            # This is where we'd normally invoke the actual app
            # For POC, we'll simulate the invocation

            # End evaluation run
            self.evaluator.end_run()

            # Get results
            eval_result = self.evaluator.get_result()

            # Convert to DataFrame to see structure
            df = eval_result.to_df()

            print(f"\n📈 Raw DataFrame shape: {df.shape}")
            print(f"📈 DataFrame columns: {list(df.columns)}")
            print(f"📈 DataFrame head:\n{df.head()}")

            # Convert to dict for easier inspection
            if not df.empty:
                result_dict = df.iloc[0].to_dict()
                print("\n📋 First row as dict:")
                for key, value in result_dict.items():
                    print(f"   {key}: {value} (type: {type(value).__name__})")
            else:
                result_dict = {}
                print("📋 No results returned")

            return {
                "prompt": prompt,
                "response": response,
                "evaluation_available": True,
                "raw_dataframe_info": {
                    "shape": df.shape,
                    "columns": list(df.columns),
                },
                "raw_results": result_dict,
                "evaluation_object_type": str(type(eval_result)),
            }

        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            import traceback

            traceback.print_exc()

            return {
                "prompt": prompt,
                "response": response,
                "evaluation_available": False,
                "error": str(e),
            }

    def get_token_usage(self) -> dict:
        """Return empty token usage for POC."""
        return {"prompt_tokens": 0, "response_tokens": 0, "total_tokens": 0}
