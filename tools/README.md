# Maestro Validation Tools

## Mermaid Validation

Validates that generated Mermaid diagrams have correct syntax and will render properly.

### Quick Start: Validate a Generated Diagram

1. **Generate a Mermaid diagram from your workflow:**
   ```bash
   maestro mermaid workflow.yaml > workflow.mmd
   ```

2. **Validate the generated diagram:**
   ```bash
   node tools/validate-mermaid.js workflow.mmd
   ```

3. **See the result:**
   ```bash
   ✅ VALID: workflow.mmd
   ```
   or
   ```bash
   ❌ INVALID: workflow.mmd
      Error: Parse error on line 5...
   ```

### Full Validation (All Workflows)

```bash
# Validates all workflow files in the repository
./tools/check-mermaid.sh
```

This will:
- Auto-install dependencies (first run only)
- Generate Mermaid diagrams for all workflows
- Validate each diagram's syntax
- Show results in a table format

### Setup

Dependencies are auto-installed by `check-mermaid.sh` on first run.

Or install manually:
```bash
cd tools && npm install
```

### Common Validation Errors

**Spaces in node IDs** (flowcharts):
```mermaid
# ❌ Invalid
flowchart LR
  My Agent --> Another Step

# ✅ Valid
flowchart LR
  agent1["My Agent"] --> step2["Another Step"]
```

**Note:** Maestro generates sequence diagrams by default, which handle spaces correctly.

