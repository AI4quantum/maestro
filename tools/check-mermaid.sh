#!/usr/bin/env bash

# Runs mermaid, and composes markdown summary for github action

if [ -z "$GITHUB_STEP_SUMMARY" ]
then
    GITHUB_STEP_SUMMARY=$(mktemp)
fi

declare -i fail=0
WORKFLOW_FILES=$(find . -path "./.venv" -prune -o -path "./.github/workflows" -prune -o -name '*workflow*.yaml' -print)
AGENT_FILES=$(find . -path "./.venv" -prune -o -path "./.github/workflows" -prune -o -name '*agents*.yaml' -print)
EXCLUDE_FILES=("./tests/yamls/workflowrun/simple_workflow_run.yaml"
	       "./operator/config/crd/bases/maestro.ai4quantum.com_workflowruns.yaml"
	       "./operator/config/crd/bases/maestro.ai4quantum.com_workflows.yaml"
	       "./operator/config/crd/bases/maestro.ai4quantum.com_agents.yaml"
	       "./operator/config/rbac/workflowrun_editor_role.yaml"
	       "./operator/config/rbac/workflowrun_viewer_role.yaml"
	       "./operator/config/samples/maestro_v1alpha1_workflowrun.yaml"
	       "./operator/test/config/test-workflowrun.yaml")

echo "|Filename|Type|Stats|" >> "$GITHUB_STEP_SUMMARY"
echo "|---|---|---|" >> "$GITHUB_STEP_SUMMARY"

# Generate mermaid for workflows
# TODO Consolidate duplication
for f in $WORKFLOW_FILES
do
    if ! printf '%s\n' "${EXCLUDE_FILES[@]}" | grep -q "^$f$"; then
        if ! uv run maestro mermaid --verbose "$f"
        then
          RESULT="FAIL ❌"
          fail+=1
        else
          RESULT="PASS ✅"
        fi
        echo "|$f|workflow|$RESULT|" >> "$GITHUB_STEP_SUMMARY"
    fi
done

if [ -z "$CI" ];
 then
  cat "$GITHUB_STEP_SUMMARY"
fi

exit $fail
