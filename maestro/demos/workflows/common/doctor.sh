#!/bin/bash

echo "🔍 Checking environment..."

# ✅ Check if `maestro` is installed inside Poetry's virtual environment
if poetry run which maestro &> /dev/null; then
    echo "✅ Maestro CLI is installed: $(poetry run which maestro)"
else
    echo "❌ Maestro CLI not found! Please install it using:"
    echo "   cd maestro && poetry install"
    exit 1
fi

echo "✅ Environment check passed!"
