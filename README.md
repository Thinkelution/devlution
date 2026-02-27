# Devlution

**AI-Augmented Developer Workflow Framework**

Devlution automates the path from **issue → code → test → PR → merge** with clearly defined human supervision gates. It is a CLI-first, agent-orchestrated framework that drops into any existing repository with a single config file.

---

## What Devlution Does

Devlution connects your issue tracker, codebase, and CI/CD pipeline through a chain of specialized AI agents:

```
GitHub Issue → Planner → Coder → Reviewer → Tester → Human Gate → PR
```

Each agent has one job, scores its own confidence, and escalates to humans when uncertain. Every action is logged to an immutable audit trail.

### Key Capabilities

- **Automated task decomposition** — Issues are broken into structured, executable subtasks
- **AI code generation** — Code is written respecting your style guide and existing patterns
- **Automated code review** — Diffs are evaluated against correctness, security, style, coverage, and side-effect rubrics
- **Test generation and execution** — Targeted tests for changed code with coverage tracking
- **Automated debugging** — CI failures and Sentry alerts trigger root-cause analysis and patches
- **Human supervision gates** — Pipeline blocks at configurable checkpoints for human approval
- **Full audit trail** — Every agent action is logged with timestamps, tokens, and confidence scores

---

## Quick Start

### Installation

```bash
pip install devlution
```

Or install from source:

```bash
git clone https://github.com/thinkelution/devlution.git
cd devlution
pip install -e ".[dev]"
```

### Initialize in Your Project

```bash
cd your-project
devlution init --language python --ci github-actions --integrations github,slack
```

This creates:
- `devlution.yaml` — configuration file (edit to customize)
- `.devlution/` — local directory for audit logs and prompt overrides
- `.github/workflows/devlution.yaml` — CI pipeline (if `--ci` specified)

### Run the Pipeline

```bash
# Set your API key
export ANTHROPIC_API_KEY=your-key-here

# Run from a GitHub issue
devlution run --trigger github_issue --issue 42

# Run manually
devlution run --trigger manual --verbose
```

### Run a Single Agent

```bash
devlution agent coder --task "Add input validation to /api/users"
devlution agent tester --files src/api/users.py
devlution agent debugger --log ci_failure.txt
```

### Manage Gates

```bash
devlution gate approve --id pre-merge-staging
devlution gate reject --id pre-merge-staging --reason "Needs security review"
```

### View Audit Log

```bash
devlution audit --last 20
devlution status
```

---

## Configuration

All behavior is controlled from `devlution.yaml`:

```yaml
project:
  name: "my-service"
  language: "python"
  test_command: "pytest"
  lint_command: "ruff check ."
  main_branch: "main"

llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  max_tokens: 8192
  temperature: 0.2

agents:
  planner:
    enabled: true
    max_subtasks: 10
  coder:
    enabled: true
    max_iterations: 3
    style_guide: ".cursor/rules"
  reviewer:
    enabled: true
    auto_approve_threshold: 0.92
    block_on: ["security", "data_loss"]
  tester:
    enabled: true
    coverage_threshold: 80
  debugger:
    enabled: true
    max_fix_attempts: 3

supervision:
  gates:
    - id: "pre-merge-staging"
      trigger: "before_merge_to_staging"
      type: "human_approval"
      notify: ["slack"]
      timeout_hours: 24

pipeline:
  flow: [planner, coder, reviewer, tester, "gate:pre-merge-staging"]
  triggers:
    - "on": "github_issue"
      label: "ai-task"
      flow: [planner, coder, reviewer, tester, "gate:pre-merge-staging"]
```

See `devlution/templates/configs/devlution.yaml` for the full reference config with all options.

---

## Architecture

### Agent Pipeline

```
┌─────────┐    ┌───────┐    ┌──────────┐    ┌────────┐    ┌──────┐    ┌────┐
│ Planner │───→│ Coder │───→│ Reviewer │───→│ Tester │───→│ Gate │───→│ PR │
└─────────┘    └───────┘    └──────────┘    └────────┘    └──────┘    └────┘
                  ↑              │               │
                  │     request_ │          fail │
                  │     changes  │               ↓
                  └──────────────┘         ┌──────────┐
                                           │ Debugger │
                                           └──────────┘
```

### Design Principles

1. **Agent-per-concern** — Each agent has one job; no god agents
2. **Config-first** — Everything controlled from `devlution.yaml`; no hardcoded logic
3. **Confidence-gated** — Agents self-score; low-confidence tasks escalate automatically
4. **Observable by default** — Every action is logged, traced, and reviewable
5. **Escape hatches everywhere** — Humans can override any automated decision

### Tech Stack

| Layer | Technology |
|---|---|
| CLI | Python + Typer |
| Agent Orchestration | LangGraph |
| LLM Calls | Anthropic Python SDK |
| GitHub Integration | PyGitHub |
| Notifications | Slack Bolt SDK |
| LLM Observability | Langfuse |
| Config Parsing | Pydantic v2 + PyYAML |
| Testing | pytest |

---

## Project Structure

```
devlution/
├── cli/                    # Typer CLI commands
│   ├── main.py             # Entry point: `devlution <command>`
│   └── commands/           # init, run, agent, status, gate, audit
├── agents/                 # AI agent implementations
│   ├── base.py             # BaseAgent with LLM calls, confidence scoring
│   ├── planner.py          # Issue → task breakdown
│   ├── coder.py            # Task → code implementation
│   ├── reviewer.py         # Diff → review decision
│   ├── tester.py           # Code → test generation + execution
│   └── debugger.py         # Failure → root cause + patch
├── orchestrator/           # LangGraph pipeline
│   ├── graph.py            # State machine definition
│   ├── state.py            # PipelineState dataclass
│   ├── router.py           # Conditional edge logic
│   └── checkpoints.py      # Gate checkpoint management
├── integrations/           # External service connectors
│   ├── github/             # Issues, PRs, labels
│   ├── slack.py            # Approval messages
│   ├── sentry.py           # Error ingestion
│   └── jira.py             # Ticket sync
├── tools/                  # Agent tool implementations
│   ├── file_editor.py      # Safe file read/write/patch
│   ├── git_ops.py          # Branch, commit, push
│   ├── code_executor.py    # Subprocess with timeout
│   └── static_analysis.py  # Lint/typecheck parsing
├── supervision/            # Human oversight layer
│   ├── gates.py            # Gate definitions + approval logic
│   ├── confidence.py       # Confidence score computation
│   └── audit_log.py        # Immutable JSONL decision log
├── templates/              # Versioned templates
│   ├── prompts/            # Agent system prompts (Markdown)
│   ├── configs/            # Default devlution.yaml
│   └── ci/                 # GitHub Actions / GitLab CI templates
└── observability.py        # Langfuse tracing integration
```

---

## Integrations

### GitHub

Set `GITHUB_TOKEN` to enable:
- Automatic issue context fetching
- PR creation with AI-generated labels
- Inline review comments at specific lines
- Reviewer assignment

### Slack

Set `DEVLUTION_SLACK_TOKEN` to enable:
- Interactive approval request messages (approve/reject buttons)
- Pipeline status notifications

### Sentry

Set `SENTRY_AUTH_TOKEN` to enable:
- Automatic error event ingestion
- Structured failure logs for the Debugger Agent

### Jira

Set `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` to enable:
- Ticket creation from pipeline events
- Status transition sync

### Langfuse (Observability)

Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` to enable:
- LLM call tracing with token and latency metrics
- Pipeline-level trace grouping

---

## CI/CD

### GitHub Actions

Generated by `devlution init --ci github-actions`:

```yaml
# Triggers on issues labeled 'ai-task'
on:
  issues:
    types: [labeled]

steps:
  - uses: actions/checkout@v4
  - run: pip install devlution
  - run: devlution run --trigger github_issue --issue ${{ github.event.issue.number }}
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GitLab CI

Generated by `devlution init --ci gitlab-ci`.

---

## Customizing Prompts

Agent prompts are versioned Markdown files in `devlution/templates/prompts/`. To override for your project:

1. Create `.devlution/prompts/` in your repo
2. Copy the prompt you want to customize (e.g., `coder.md`)
3. Edit it — the agent will use your version instead of the default

This lets you tune agent behavior without forking Devlution.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key for LLM calls |
| `GITHUB_TOKEN` | For GitHub | GitHub personal access token |
| `DEVLUTION_SLACK_TOKEN` | For Slack | Slack Bot token |
| `SENTRY_AUTH_TOKEN` | For Sentry | Sentry authentication token |
| `JIRA_BASE_URL` | For Jira | Jira instance URL |
| `JIRA_EMAIL` | For Jira | Jira account email |
| `JIRA_API_TOKEN` | For Jira | Jira API token |
| `LANGFUSE_PUBLIC_KEY` | For observability | Langfuse public key |
| `LANGFUSE_SECRET_KEY` | For observability | Langfuse secret key |

---

## Development

```bash
# Clone and install
git clone https://github.com/thinkelution/devlution.git
cd devlution
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Type check
mypy devlution/
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

Built by [Thinkelution](https://github.com/thinkelution).
