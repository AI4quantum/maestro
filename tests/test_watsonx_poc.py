#!/usr/bin/env python3
"""
Simple test script to run the watsonx POC agent and see output structure.
"""

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from maestro.agents.watsonx_poc_agent import WatsonxPocAgent


async def test_watsonx_poc():
    """Test the watsonx POC agent with sample data."""

    # Create agent configuration
    agent_config = {
        "metadata": {"name": "test-poc"},
        "spec": {"model": "test-model", "framework": "custom", "mode": "local"},
    }

    # Create agent instance
    agent = WatsonxPocAgent(agent_config)

    # Test data
    test_cases = [
        {
            "prompt": "What is quantum computing?",
            "response": "Quantum computing is a type of computation that uses quantum mechanical phenomena like superposition and entanglement to process information.",
            "context": ["Quantum computers use qubits", "Classical computers use bits"],
        },
        {
            "prompt": "How do you make a sandwich?",
            "response": "To make a sandwich, put ingredients between two slices of bread.",
            "ground_truth": "A sandwich is made by placing fillings between bread slices.",
        },
    ]

    print("🧪 Testing Watsonx POC Agent\n")
    print("=" * 50)

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 Test Case {i}:")
        print("-" * 30)

        # Run evaluation
        result = await agent.run(**test_case)

        print(f"\n📊 Result {i}:")
        print("-" * 20)

        # Pretty print the result
        import json

        print(json.dumps(result, indent=2, default=str))

        print("\n" + "=" * 50)


if __name__ == "__main__":
    print("🚀 Starting Watsonx POC Test")
    asyncio.run(test_watsonx_poc())
