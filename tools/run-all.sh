#!/usr/bin/env bash

# Runs all the tools and checks

list=("./tools/check-schemas.sh" "./tools/check-mermaid.sh" "./tools/run-meta-agent.sh")
   
for item in "${list[@]}"; do
    echo "Running 🏃🏽‍♀️‍➡️ $item"
    eval $item
done