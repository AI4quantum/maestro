# TODO Report - Maestro Codebase

*Generated on: $(date)*

## Overview

This report contains all TODO items found throughout the Maestro codebase, organized by category and file location.

**Total TODOs found: 35**

## Summary by Category

| Category | Count | Description |
|----------|-------|-------------|
| **Core Python Code** | 11 | Main Maestro functionality in `src/maestro/` |
| **Demo Code** | 8 | Example implementations in `demos/` |
| **Test Code** | 6 | Test files and test-related TODOs |
| **Go/Kubernetes** | 8 | Operator and Kubernetes-related code |
| **Shell Scripts** | 3 | Build and utility scripts |
| **Documentation** | 1 | README and documentation files |

---

## 1. Core Python Code (`src/maestro/`)

### `src/maestro/agents/agent.py`
- **Line 19**: `# TODO: Review which attributes belong in base class vs subclasses`
  - **Category**: Code Architecture
  - **Description**: Need to review and refactor class structure

### `src/maestro/agents/openai_agent.py`
- **Line 123**: `# TODO: Large context windows need checking. Including with LitelLM enabled`
  - **Category**: Performance/Optimization
  - **Description**: Context window validation needed for different LLM backends

- **Line 185**: `# TODO: Cleanup streaming vs non-streaming`
  - **Category**: Code Refactoring
  - **Description**: Consolidate streaming and non-streaming code paths

- **Line 213**: `# TODO: Extend or make generic for more settings`
  - **Category**: Feature Enhancement
  - **Description**: Make settings configuration more generic

- **Line 296**: `# TODO: Refactor some stream handling into common routine across backends? Code verbose`
  - **Category**: Code Refactoring
  - **Description**: Reduce code duplication in stream handling across different backends

### `src/maestro/agents/openai_mcp.py`
- **Line 13**: `# TODO: can this be refactored so we can support more types of agents`
  - **Category**: Code Architecture
  - **Description**: Refactor to support additional agent types beyond current implementation

### `src/maestro/agents/crewai_agent.py`
- **Line 50**: `# TODO: Add additional properties later. for now using naming:`
  - **Category**: Feature Enhancement
  - **Description**: Extend agent properties beyond current naming convention

- **Line 159**: `# TODO: Add API key handling if needed by the LLM provider`
  - **Category**: Security/Configuration
  - **Description**: Implement proper API key management for LLM providers

- **Line 191**: `# TODO: Add memory, cache, etc. configuration if needed`
  - **Category**: Feature Enhancement
  - **Description**: Add configuration options for memory and caching

### `src/maestro/agents/beeai_agent.py`
- **Line 86**: `# TODO: Unused currently`
  - **Category**: Code Cleanup
  - **Description**: Remove or implement unused code

---

## 2. Demo Code (`demos/`)

### `demos/agents/crewai/activity_planner/activity_planner.py`
- **Line 13**: `# TODO Make a more representative crew agent. This is simple`
  - **Category**: Demo Enhancement
  - **Description**: Improve the demo agent to be more representative of real-world usage

- **Line 14**: `# TODO decorators use config/agents.yaml & config/tasks.yaml. Former clashes in name which causes yaml validation error`
  - **Category**: Configuration
  - **Description**: Fix naming conflicts in YAML configuration files

- **Line 15**: `# TODO decorators cause PyLance errors`
  - **Category**: Development Tools
  - **Description**: Resolve PyLance static analysis errors with decorators

- **Line 32**: `# TODO Set model/URL from configuration`
  - **Category**: Configuration
  - **Description**: Move hardcoded model/URL to configuration files

- **Line 38**: `# TODO PyLance issue - missing self() but fails with crewai decorators if added`
  - **Category**: Development Tools
  - **Description**: Fix PyLance type checking issues with crewai decorators

- **Line 93**: `# TODO: disable verbose when working well`
  - **Category**: Debugging
  - **Description**: Reduce verbose output once functionality is stable

### `demos/agents/crewai/generic/generic_agent.py`
- **Line 22**: `# TODO Set model/URL from configuration`
  - **Category**: Configuration
  - **Description**: Move hardcoded model/URL to configuration files

- **Line 67**: `# TODO: disable verbose when working well`
  - **Category**: Debugging
  - **Description**: Reduce verbose output once functionality is stable

### `demos/workflows/activity-planner.ai/src/run.py`
- **Line 9**: `# TODO: dd crewai agent path to path explicitly - this should be found on path, but may require base change`
  - **Category**: Path Management
  - **Description**: Fix path resolution for crewai agent modules

---

## 3. Test Code (`tests/`)

### `tests/workflow/test_mermaid.py`
- **Line 146**: `# TODO: complete`
- **Line 288**: `#TODO complete`
- **Line 333**: `#TODO: complete`
- **Line 379**: `#TODO: complete`
- **Line 414**: `#TODO: complete`
  - **Category**: Test Completion
  - **Description**: Multiple test cases marked as incomplete, need implementation

### `tests/agents/crewai_agent/crew_dummy.py`
- **Line 7**: `# TODO: kickoff actually takes & returns a dict[str,str]`
  - **Category**: Test Accuracy
  - **Description**: Update test to match actual API signature

---

## 4. Go/Kubernetes Operator Code (`operator/`)

### `operator/internal/controller/workflowrun_controller_test.go`
- **Line 40**: `Namespace: "default", // TODO(user):Modify as needed`
- **Line 53**: `// TODO(user): Specify other spec details if needed.`
- **Line 60**: `// TODO(user): Cleanup logic after each test, like removing the resource instance.`
- **Line 79**: `// TODO(user): Add more specific assertions depending on your controller's reconciliation logic.`
  - **Category**: Test Configuration
  - **Description**: User-specific test setup and assertions needed

### `operator/internal/controller/workflowrun_controller.go`
- **Line 47**: `// TODO(user): Modify the Reconcile function to compare the state specified by`
  - **Category**: Controller Logic
  - **Description**: Implement reconciliation logic for workflow runs

### `operator/config/manager/manager.yaml`
- **Line 30**: `# TODO(user): Uncomment the following code to configure the nodeAffinity expression`
- **Line 52**: `# TODO(user): For common cases that do not require escalating privileges`
- **Line 85**: `# TODO(user): Configure the resources accordingly based on the project requirements.`
  - **Category**: Kubernetes Configuration
  - **Description**: Production-ready Kubernetes configuration needed

### `operator/config/prometheus/monitor.yaml`
- **Line 17**: `# TODO(user): The option insecureSkipVerify: true is not recommended for production since it disables`
  - **Category**: Security
  - **Description**: Configure proper TLS for production monitoring

### `operator/cmd/main.go`
- **Line 105**: `// TODO(user): TLSOpts is used to allow configuring the TLS config used for the server. If certificates are`
  - **Category**: Security
  - **Description**: Configure TLS certificates for the operator server

---

## 5. Shell Scripts (`tools/`)

### `tools/check-schemas.sh`
- **Line 24**: `# TODO Consolidate duplication`
  - **Category**: Code Cleanup
  - **Description**: Remove duplicate code in schema checking scripts

### `tools/check-mermaid.sh`
- **Line 27**: `# TODO Consolidate duplication`
  - **Category**: Code Cleanup
  - **Description**: Remove duplicate code in mermaid checking scripts

### `tools/run-demos.sh`
- **Line 82**: `# TODO: Demos may need complex setup/environment. For now they can create their own`
  - **Category**: Demo Infrastructure
  - **Description**: Improve demo setup and environment management

---

## 6. Demo Scripts

### `demos/workflows/openai-mcp.ai/test.sh`
- **Line 87**: `# TODO: Setup langfuse for observability (if applicable)`
  - **Category**: Observability
  - **Description**: Integrate Langfuse for better observability and monitoring

- **Line 108**: `# TODO: Validation could be improved - simple grep check initially`
  - **Category**: Test Quality
  - **Description**: Improve validation logic beyond simple grep checks

---

## 7. Documentation

### `demos/workflows/activity-planner.ai/README.md`
- **Line 1**: `TODO the demo does not currently function out of the box as the workflow schema / automation are not supported by the demo as of yet. Merging this early and will address after we've moved name/repos.`
  - **Category**: Demo Functionality
  - **Description**: Demo needs to be updated to work with current workflow schema

---

## Priority Recommendations

### High Priority
1. **Security Issues**: API key handling, TLS configuration for production
2. **Core Functionality**: Large context window validation, streaming cleanup
3. **Test Completion**: Complete the 5 incomplete test cases in `test_mermaid.py`

### Medium Priority
1. **Code Refactoring**: Stream handling consolidation, agent type support
2. **Configuration**: Move hardcoded values to configuration files
3. **Demo Functionality**: Fix demo to work out of the box

### Low Priority
1. **Development Tools**: PyLance error resolution
2. **Code Cleanup**: Remove unused code, consolidate duplication
3. **Documentation**: Update README files

---

## Action Items

1. **Immediate**: Address security-related TODOs for production readiness
2. **Short-term**: Complete test cases and fix demo functionality
3. **Long-term**: Refactor code for better maintainability and extensibility

---

*Report generated by automated TODO scanner* 