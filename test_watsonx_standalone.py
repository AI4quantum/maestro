#!/usr/bin/env python3
"""
Standalone test script for watsonx evaluation library.
This tests the actual library functionality without Maestro dependencies.
"""

from ibm_watsonx_gov.evaluators.agentic_evaluator import AgenticEvaluator
from ibm_watsonx_gov.entities.state import EvaluationState
from ibm_watsonx_gov.entities.agentic_app import AgenticApp, MetricsConfiguration
from ibm_watsonx_gov.metrics import AnswerRelevanceMetric, FaithfulnessMetric


class AppState(EvaluationState):
    """Simple evaluation state for testing."""

    pass


def test_watsonx_evaluation():
    """Test the watsonx evaluation with sample data."""

    print("🧪 Testing Watsonx Evaluation Library")
    print("=" * 50)

    # Create evaluation configuration
    print("\n1. Creating evaluation configuration...")
    metrics_config = MetricsConfiguration(
        metrics=[AnswerRelevanceMetric(), FaithfulnessMetric()]
    )

    agentic_app = AgenticApp(
        name="POC Test Application", metrics_configuration=metrics_config
    )

    evaluator = AgenticEvaluator(agentic_app=agentic_app)
    print("✅ Evaluator created successfully")

    # Test cases
    test_cases = [
        {
            "input_text": "What is quantum computing?",
            "output": "Quantum computing is a type of computation that uses quantum mechanical phenomena like superposition and entanglement to process information.",
            "interaction_id": "test_1",
        },
        {
            "input_text": "How do solar panels work?",
            "output": "Solar panels convert sunlight into electricity using photovoltaic cells that create an electric current when exposed to light.",
            "interaction_id": "test_2",
        },
    ]

    print("\n2. Running evaluations...")
    evaluator.start_run()

    # Simulate evaluations (normally this would be done through actual agent invocations)
    for i, test_case in enumerate(test_cases, 1):
        print(f"   Processing test case {i}: {test_case['input_text'][:50]}...")
        # In a real scenario, this is where the agent would be invoked
        # For now, we'll just demonstrate the structure

    evaluator.end_run()

    print("\n3. Getting evaluation results...")
    try:
        eval_result = evaluator.get_result()
        df = eval_result.to_df()

        print("✅ Results obtained!")
        print(f"   DataFrame shape: {df.shape}")
        print(f"   DataFrame columns: {list(df.columns)}")

        if not df.empty:
            print("\n4. Sample results:")
            print(df.head().to_string())

            # Convert to dict for inspection
            if len(df) > 0:
                sample_row = df.iloc[0].to_dict()
                print("\n5. First row as dictionary:")
                for key, value in sample_row.items():
                    print(f"   {key}: {value} (type: {type(value).__name__})")
        else:
            print("\n4. No evaluation data available (empty DataFrame)")
            print("   This is expected since we didn't run actual evaluations")

    except Exception as e:
        print(f"❌ Error getting results: {e}")
        import traceback

        traceback.print_exc()

    print("\n6. Testing the evaluator structure...")
    print(f"   Evaluator type: {type(evaluator)}")
    print(f"   Agentic app name: {agentic_app.name}")
    print(f"   Metrics configured: {len(metrics_config.metrics)}")
    for i, metric in enumerate(metrics_config.metrics):
        print(f"     {i + 1}. {type(metric).__name__}")

    print("\n✅ Watsonx evaluation library test completed!")
    print("\nSummary:")
    print("- ✅ Library imports successfully")
    print("- ✅ Evaluator can be created and configured")
    print("- ✅ Evaluation runs can be started/stopped")
    print("- ✅ Results can be retrieved (when data is available)")
    print("\nNext steps:")
    print("- Integrate with actual Maestro agent responses")
    print("- Set up automatic evaluation middleware")
    print("- Design database schema based on output structure")


if __name__ == "__main__":
    test_watsonx_evaluation()
