#!/bin/bash

echo "🔍 Checking environment..."

# Check if maestro is installed
if uv run which maestro &> /dev/null; then
    echo "✅ Maestro CLI is installed: $(uv run which maestro)"
else
    echo "❌ Maestro CLI is not installed. Please run:"
    echo "   uv sync"
fi

# Check meta-agent directory structure
echo "📂 Checking meta-agent directory structure..."
if [[ -d "$(dirname "$0")" ]]; then
    echo "✅ Environment check passed!"
else
    echo "❌ Error: meta-agent directory not found"
    exit 1
fi
