#!/usr/bin/env bash

if [ -z "$GITHUB_STEP_SUMMARY" ]; then
    GITHUB_STEP_SUMMARY=$(mktemp)
fi

declare -i fail=0
declare -i validation_fail=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$SCRIPT_DIR/node_modules" ]; then
    echo "Installing validation dependencies..."
    (cd "$SCRIPT_DIR" && npm install --silent)
fi

WORKFLOW_FILES=$(find . -path "./.venv" -prune -o -path "./.github/workflows" -prune -o -name '*workflow*.yaml' -print)
EXCLUDE_FILES=("./tests/yamls/workflowrun/simple_workflow_run.yaml"
	       "./operator/config/crd/bases/maestro.ai4quantum.com_workflowruns.yaml"
	       "./operator/config/crd/bases/maestro.ai4quantum.com_workflows.yaml"
	       "./operator/config/crd/bases/maestro.ai4quantum.com_agents.yaml"
	       "./operator/config/rbac/workflowrun_editor_role.yaml"
	       "./operator/config/rbac/workflowrun_viewer_role.yaml"
	       "./operator/config/samples/maestro_v1alpha1_workflowrun.yaml"
	       "./operator/test/config/test-workflowrun.yaml")

echo "|Filename|Type|Generation|Validation|" >> "$GITHUB_STEP_SUMMARY"
echo "|---|---|---|---|" >> "$GITHUB_STEP_SUMMARY"

for f in $WORKFLOW_FILES; do
    if ! printf '%s\n' "${EXCLUDE_FILES[@]}" | grep -q "^$f$"; then
        MMD_FILE="${f%.yaml}.mmd"
        
        if ! MERMAID_OUTPUT=$(PYTHONWARNINGS=ignore uv run maestro mermaid --silent "$f" 2>&1); then
            GEN_RESULT="FAIL ❌"
            VAL_RESULT="SKIP ⏭️"
            fail+=1
        else
            GEN_RESULT="PASS ✅"
            echo "$MERMAID_OUTPUT" > "$MMD_FILE"
            
            if [ -f "$MMD_FILE" ]; then
                if node "$SCRIPT_DIR/validate-mermaid.js" "$MMD_FILE" > /dev/null 2>&1; then
                    VAL_RESULT="VALID ✅"
                else
                    VAL_RESULT="INVALID ❌"
                    validation_fail+=1
                    fail+=1
                    echo ""
                    echo "Validation failed for $MMD_FILE:"
                    node "$SCRIPT_DIR/validate-mermaid.js" "$MMD_FILE"
                fi
            else
                VAL_RESULT="NOT FOUND ⚠️"
            fi
        fi
        echo "|$f|workflow|$GEN_RESULT|$VAL_RESULT|" >> "$GITHUB_STEP_SUMMARY"
    fi
done

if [ -z "$CI" ]; then
    cat "$GITHUB_STEP_SUMMARY"
fi

if [ $validation_fail -gt 0 ]; then
    echo ""
    echo "❌ $validation_fail Mermaid diagram(s) failed syntax validation"
    echo "   Agent/step names with spaces or special characters need sanitization."
fi

exit $fail
