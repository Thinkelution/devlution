# Devlution Architecture Overview

This document describes the system architecture for teams evaluating Devlution for adoption.

---

## System Overview

Devlution is a **CLI-first, agent-orchestrated framework** that automates software development workflows. It sits between your issue tracker and your codebase, using AI agents to plan, code, review, test, and debug — with human approval gates at every critical juncture.

```
┌──────────────────────────────────────────────────────────────────┐
│                         Devlution Pipeline                       │
│                                                                  │
│  Trigger ──→ Planner ──→ Coder ──→ Reviewer ──→ Tester ──→ Gate │
│  (Issue)      (AI)        (AI)      (AI)         (AI)    (Human) │
│                                                              │   │
│                                                              ↓   │
│                                                          Create  │
│                                                            PR    │
└──────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. CLI Layer (`devlution/cli/`)

The command-line interface built with Typer. Entry point for all operations:

- `devlution init` — project setup
- `devlution run` — full pipeline execution
- `devlution agent` — single-agent execution
- `devlution gate` — human approval management
- `devlution audit` — audit trail inspection

### 2. Agent Layer (`devlution/agents/`)

Five specialized agents, each subclassing `BaseAgent`:

| Agent | Input | Output | Purpose |
|-------|-------|--------|---------|
| Planner | GitHub issue | Task list with file hints | Decomposes issues into executable subtasks |
| Coder | Single task | File changes + commit | Implements code respecting project style |
| Reviewer | Git diff | Decision + comments | Evaluates changes against quality rubric |
| Tester | Changed files | Test results + coverage | Generates and runs targeted tests |
| Debugger | Failure log | Root cause + patch | Analyzes failures and produces fixes |

### 3. Orchestration Layer (`devlution/orchestrator/`)

Built on **LangGraph**, the orchestrator defines the pipeline as a state machine:

- **State** (`state.py`): `PipelineState` dataclass tracking the full context
- **Graph** (`graph.py`): Node and edge definitions with conditional routing
- **Router** (`router.py`): Decision functions that determine the next step
- **Checkpoints** (`checkpoints.py`): Human gate management

### 4. Supervision Layer (`devlution/supervision/`)

The human oversight system:

- **Gates**: Block pipeline until a human approves (via Slack, GitHub, or CLI)
- **Confidence Scoring**: Agents self-evaluate; low scores trigger automatic escalation
- **Audit Log**: Append-only JSONL recording every pipeline action

### 5. Integration Layer (`devlution/integrations/`)

Connectors for external services:

- **GitHub**: Issue context, PR creation, review comments, labels
- **Slack**: Interactive approval messages with buttons
- **Sentry**: Error event ingestion for the Debugger Agent
- **Jira**: Optional ticket sync

### 6. Tools Layer (`devlution/tools/`)

Safe wrappers for system operations used by agents:

- **File Editor**: Read/write/patch with audit logging
- **Git Ops**: Branch, commit, push via subprocess
- **Code Executor**: Timeout-bounded command execution
- **Static Analysis**: Lint/typecheck output parsing

---

## Data Flow

### Standard Issue Pipeline

```
1. Trigger: GitHub issue labeled 'ai-task'
2. Planner reads issue, searches codebase, produces task list
3. For each task:
   a. Coder reads files, implements changes, runs lint
   b. Reviewer evaluates diff against rubric
      - If approved → continue
      - If request_changes → back to Coder (up to max_iterations)
      - If low confidence → escalate to human
   c. Tester generates tests, runs suite, checks coverage
      - If pass → continue
      - If fail → Debugger agent (up to max_fix_attempts)
4. Gate: pipeline blocks for human approval
5. PR created with labels and review requested
```

### Failure Recovery Pipeline

```
1. Trigger: CI failure or Sentry alert
2. Debugger parses error, reads source, hypothesizes causes
3. Generates minimal fix for top hypothesis
4. Tester re-runs tests to verify
5. Reviewer evaluates the fix
6. Gate: human approval before merge
```

---

## Security Model

- **API keys** are never stored in config — always via environment variables
- **File operations** are sandboxed through the `file_editor` module
- **Code execution** runs with configurable timeouts (default 5 minutes)
- **Agents cannot modify files** outside their declared scope without re-planning
- **Audit log** provides complete traceability of every automated action
- **Human gates** ensure no code reaches production without explicit approval

---

## Deployment Options

### 1. Local Development

Run Devlution directly on your machine:

```bash
pip install devlution
devlution init
devlution run --trigger manual
```

### 2. CI/CD Integration

Run as part of your existing pipeline:

- **GitHub Actions**: Auto-generated workflow triggers on issue labels
- **GitLab CI**: Pipeline stage with artifact collection
- **Self-hosted runners**: Any environment with Python 3.11+

### 3. Scheduled Runs

Configure cron-based triggers for nightly test runs:

```yaml
pipeline:
  triggers:
    - "on": "schedule"
      cron: "0 2 * * *"
      flow: [tester, reviewer]
```

---

## Customization Points

| What | How |
|------|-----|
| Agent behavior | Override prompts in `.devlution/prompts/` |
| Pipeline flow | Edit `pipeline.flow` and `pipeline.triggers` in config |
| Confidence thresholds | Adjust `auto_approve_threshold`, gate `threshold` |
| Tool configuration | Change `test_command`, `lint_command` in project config |
| Integrations | Enable/disable per-integration in config |
| LLM model | Switch models in `llm.model` / `llm.fallback_model` |

---

## Observability

When Langfuse is configured, every LLM call emits:

- Model used
- Input/output token counts
- Latency in milliseconds
- Agent name and pipeline ID

All entries are grouped by pipeline run for end-to-end traceability.

The local audit log (`.devlution/audit.jsonl`) provides the same data without external dependencies:

```json
{"ts":"2026-02-27T10:00:00Z","pipeline_id":"abc123","agent":"coder","action":"llm_call","tokens_used":1842,"confidence":0.91,"duration_ms":4200}
```
