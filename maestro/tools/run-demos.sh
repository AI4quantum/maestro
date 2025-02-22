#!/bin/bash

echo "🚀 Running all demos in CI..."
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "📂 Running from: $REPO_ROOT"

WORKFLOWS_DIR="$REPO_ROOT/maestro/demos/workflows"
COMMON_DIR="$REPO_ROOT/maestro/demos/workflows/common"

if [[ ! -d "$WORKFLOWS_DIR" ]]; then
    echo "❌ Error: Workflows directory not found at $WORKFLOWS_DIR"
    exit 1
fi

if [[ ! -d "$COMMON_DIR" ]]; then
    echo "❌ Error: Common directory not found at $COMMON_DIR"
    exit 1
fi

echo "🔍 Verifying Maestro installation..."
cd "$REPO_ROOT/maestro"

# Test if maestro works with or without poetry
if poetry run maestro --help &>/dev/null; then
    MAESTRO_CMD="poetry run maestro"
elif maestro --help &>/dev/null; then
    MAESTRO_CMD="maestro"
else
    echo "❌ Error: maestro is not running correctly!"
    exit 1
fi

echo "✅ Maestro is running correctly using: $MAESTRO_CMD"

EXPECTED_TESTS=0
TEST_COUNT=0

# Find all workflow demo folders inside `maestro/demos/workflows/`
for demo in $(find "$WORKFLOWS_DIR" -mindepth 1 -maxdepth 1 -type d); do
    # ✅ Skip the `common/` directory
    if [[ "$demo" == "$COMMON_DIR" ]]; then
        echo "⚠️ Skipping common/ directory..."
        continue
    fi

    echo "🔍 Running tests for $demo"
    ((EXPECTED_TESTS++))  # Expecting each demo to be tested

    # Run shared doctor.sh
    echo "🩺 Running common doctor.sh for $demo..."
    cd "$REPO_ROOT/maestro"
    poetry run bash "$COMMON_DIR/doctor.sh" || { echo "❌ doctor.sh failed for $demo"; exit 1; }

    # Run shared test.sh with the demo folder as an argument
    echo "🧪 Running common test.sh for $demo..."
    cd "$REPO_ROOT/maestro"
    env MAESTRO_DEMO_OLLAMA_MODEL="ollama/llama3.2:3b" echo "" | poetry run bash "$COMMON_DIR/test.sh" "$demo" || { echo "❌ test.sh failed for $demo"; exit 1; }
    ((TEST_COUNT++))
done

# Print success message only if ALL expected tests were run
if [[ "$TEST_COUNT" -eq "$EXPECTED_TESTS" && "$EXPECTED_TESTS" -gt 0 ]]; then
    echo "✅ All $EXPECTED_TESTS tests completed successfully!"
else
    echo "❌ Error: Not all expected tests were executed! ($TEST_COUNT/$EXPECTED_TESTS)"
    exit 1
fi

# echo "🚀 Running all demos in CI..."
# REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

# echo "📂 Running from: $REPO_ROOT"

# WORKFLOWS_DIR="$REPO_ROOT/maestro/demos/workflows"

# if [[ ! -d "$WORKFLOWS_DIR" ]]; then
#     echo "❌ Error: Workflows directory not found at $WORKFLOWS_DIR"
#     exit 1
# fi

# echo "🔍 Verifying Maestro installation..."
# cd "$REPO_ROOT/maestro"

# if poetry run maestro --help &>/dev/null; then
#     MAESTRO_CMD="poetry run maestro"
# elif maestro --help &>/dev/null; then
#     MAESTRO_CMD="maestro"
# else
#     echo "❌ Error: maestro is not running correctly!"
#     exit 1
# fi

# echo "✅ Maestro is running correctly using: $MAESTRO_CMD"

# EXPECTED_TESTS=0
# TEST_COUNT=0

# for demo in $(find "$WORKFLOWS_DIR" -mindepth 1 -maxdepth 1 -type d); do
#     echo "🔍 Looking for test scripts in $demo"

#     test_dir="$demo"

#     echo "📂 Using test directory: $test_dir"

#     [[ -f "$test_dir/doctor.sh" ]] && ((EXPECTED_TESTS++))
#     [[ -f "$test_dir/test.sh" ]] && ((EXPECTED_TESTS++))

#     if [[ -f "$test_dir/doctor.sh" ]]; then
#         echo "🩺 Running doctor.sh in $test_dir..."
#         cd "$REPO_ROOT/maestro"
#         poetry run bash "$test_dir/doctor.sh" || { echo "❌ doctor.sh failed in $test_dir"; exit 1; }
#         ((TEST_COUNT++))
#     else
#         echo "⚠️ Warning: doctor.sh not found in $test_dir"
#     fi

#     if [[ -f "$test_dir/test.sh" ]]; then
#         echo "🧪 Running test.sh in $test_dir..."
#         cd "$REPO_ROOT/maestro"
#         env MAESTRO_DEMO_OLLAMA_MODEL="ollama/llama3.2:3b" poetry run bash "$test_dir/test.sh" || { echo "❌ test.sh failed in $test_dir"; exit 1; }
#         ((TEST_COUNT++))
#     else
#         echo "⚠️ Warning: test.sh not found in $test_dir"
#     fi
# done

# if [[ "$TEST_COUNT" -eq "$EXPECTED_TESTS" && "$EXPECTED_TESTS" -gt 0 ]]; then
#     echo "✅ All $EXPECTED_TESTS tests completed successfully!"
# else
#     echo "❌ Error: Not all expected tests were executed! ($TEST_COUNT/$EXPECTED_TESTS)"
#     exit 1
# fi
