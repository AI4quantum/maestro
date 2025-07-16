#!/usr/bin/env bash
#
# update_all_readme.sh
#
# This script searches the demos folder (a sibling of the tools folder)
# for directories containing both a workflow.yaml and a README.md.
# For each such directory, it runs `maestro mermaid` on workflow.yaml,
# filters out any WARNING output, and then uses Perl to replace everything
# between the existing <!-- MERMAID_START --> and <!-- MERMAID_END --> markers
# with the newly generated Mermaid diagram.
# NOTE: Demos have been moved to https://github.com/AI4quantum/maestro-demos
# This script is deprecated and will exit.
#

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "This script is deprecated. Demos have been moved to https://github.com/AI4quantum/maestro-demos"
echo "Please run this script from the maestro-demos repository instead."
exit 0

START_MARKER="<!-- MERMAID_START -->"
END_MARKER="<!-- MERMAID_END -->"

update_readme_in_dir() {
    local dir="$1"
    local workflow_file="$dir/workflow.yaml"
    local readme_file="$dir/README.md"

    if [ ! -f "$workflow_file" ] || [ ! -f "$readme_file" ]; then
        return
    fi

    echo "Processing directory: $dir"

    local mermaid_output
    mermaid_output=$(maestro mermaid "$workflow_file" --silent 2>&1 | grep -v "WARNING")
    if [ $? -ne 0 ]; then
        echo "Error generating Mermaid diagram for $workflow_file"
        return
    fi

    local triple_backticks='```'
    local code_block
    code_block=$(printf '%smermaid\n%s\n%s' "$triple_backticks" "$mermaid_output" "$triple_backticks")

    local new_block
    new_block=$(printf "%s\n%s\n%s" "$START_MARKER" "$code_block" "$END_MARKER")

    local tmp
    tmp=$(mktemp)
    perl -0777 -pe "s{<!-- MERMAID_START -->.*<!-- MERMAID_END -->}{$new_block}s" "$readme_file" > "$tmp"
    mv "$tmp" "$readme_file"
    echo "Updated $readme_file"
}

find "$DEMOS_DIR" -type f -name "workflow.yaml" | while read -r wf; do
    dir=$(dirname "$wf")
    if [ -f "$dir/README.md" ]; then
        update_readme_in_dir "$dir"
    fi
done

echo "All updates complete."
