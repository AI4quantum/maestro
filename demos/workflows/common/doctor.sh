#!/bin/bash

echo "🔍 Checking environment..."

# Check if maestro is installed
if uv run which maestro &> /dev/null; then
    echo "✅ Maestro CLI is installed: $(uv run which maestro)"
else
    echo "❌ Maestro CLI is not installed. Please run:"
    echo "   uv sync"
fi

# Check workflow directory structure
echo "📂 Checking workflow directory structure..."
if [[ -d "$(dirname "$0")" ]]; then
    echo "✅ Environment check passed!"
else
    echo "❌ Error: workflow directory not found"
    exit 1
fi
