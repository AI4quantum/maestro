#!/usr/bin/env bash

# Runs validator, and composes markdown summary for github action

if [ -z "$GITHUB_STEP_SUMMARY" ]
then
    GITHUB_STEP_SUMMARY=$(mktemp)
fi

declare -i fail=0
WORKFLOW_FILES=$(find . -path "./.venv" -prune -o -name '*workflow*.yaml' -print)
AGENT_FILES=$(find . -path "./.venv" -prune -o -name '*agents*.yaml' -print)
TOOL_FILES=$(find . -path "./.venv" -prune -o -name '*tools*.yaml' -print)


echo "|Filename|Type|Stats|" >> "$GITHUB_STEP_SUMMARY"
echo "|---|---|---|" >> "$GITHUB_STEP_SUMMARY"

EXCLUDED_FILES=("./crewai_test/src/crewai_test/config/agents.yaml"
		"./demos/agents/crewai/generic/config/agents.yaml"
		"./demos/agents/crewai/activity_planner/config/agents.yaml"
		"./operator/config/rbac/workflowrun_editor_role.yaml"
		"./operator/config/rbac/workflowrun_viewer_role.yaml")

# Check workflows
# TODO Consolidate duplication
for f in $WORKFLOW_FILES
    do
      EXCLUDE=false
      for EXCLUDED_FILE in "${EXCLUDED_FILES[@]}"; do
        if [[ "$f" == "$EXCLUDED_FILE" ]]; then
	    echo $f
            EXCLUDE=true
            break
        fi
      done
      if ! $EXCLUDE
      then
        if ! ./maestro validate "$f"
        then
          RESULT="FAIL ❌"
          fail+=1
        else
          RESULT="PASS ✅"
        fi
        echo "|$f|workflow|$RESULT|" >> "$GITHUB_STEP_SUMMARY"
      fi
    done

# Check agents
for f in $AGENT_FILES
    do
      EXCLUDE=false
      for EXCLUDED_FILE in "${EXCLUDED_FILES[@]}"; do
          if [[ "$f" == "$EXCLUDED_FILE" ]]; then
	      echo $f
              EXCLUDE=true
              break
          fi
      done
      if ! $EXCLUDE
      then
        if ! ./maestro validate "$f"
        then
          RESULT="FAIL ❌"
          fail+=1
        else
          RESULT="PASS ✅"
        fi
        echo "|$f|agent|$RESULT|" >> "$GITHUB_STEP_SUMMARY"
      fi
    done

# Check toolss
for f in $TOOL_FILES
    do
      EXCLUDE=false
      for EXCLUDED_FILE in "${EXCLUDED_FILES[@]}"; do
          if [[ "$f" == "$EXCLUDED_FILE" ]]; then
	      echo $f
              EXCLUDE=true
              break
          fi
      done
      if ! $EXCLUDE
      then
        if ! ./maestro validate "$f"
        then
          RESULT="FAIL ❌"
          fail+=1
        else
          RESULT="PASS ✅"
        fi
        echo "|$f|agent|$RESULT|" >> "$GITHUB_STEP_SUMMARY"
      fi
    done

if [ -z "$CI" ];
 then
  cat "$GITHUB_STEP_SUMMARY"
fi

exit $fail
