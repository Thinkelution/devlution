# Devlution Configuration Reference

Complete reference for all `devlution.yaml` settings.

---

## project

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | **required** | Project name |
| `language` | enum | `"python"` | `python`, `typescript`, `go`, `java` |
| `test_command` | string | `"pytest"` | Command to run tests |
| `lint_command` | string | `"ruff check ."` | Command to run linter |
| `main_branch` | string | `"main"` | Main branch name |

## llm

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | enum | `"anthropic"` | `anthropic` or `openai` |
| `model` | string | `"claude-sonnet-4-20250514"` | Primary model for agent calls |
| `fallback_model` | string | `"claude-sonnet-4-20250514"` | Fallback model for confidence scoring |
| `max_tokens` | int | `8192` | Maximum tokens per LLM call |
| `temperature` | float | `0.2` | LLM temperature (lower = more deterministic) |

## agents

### agents.planner

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the planner |
| `max_subtasks` | int | `10` | Maximum tasks per issue |

### agents.coder

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the coder |
| `max_iterations` | int | `3` | Max lint-fix cycles before escalation |
| `style_guide` | string | `".cursor/rules"` | Path to style guide file |

### agents.reviewer

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the reviewer |
| `auto_approve_threshold` | float | `0.92` | Confidence above which auto-approve is allowed |
| `block_on` | list[str] | `["security", "data_loss"]` | Categories that always require human review |

### agents.tester

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the tester |
| `frameworks` | list[str] | `["pytest"]` | Test frameworks in use |
| `coverage_threshold` | int | `80` | Minimum coverage percent required |
| `generate_on` | list[str] | `["new_file", "modified_function"]` | When to generate tests |

### agents.debugger

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable/disable the debugger |
| `max_fix_attempts` | int | `3` | Maximum debugging iterations |
| `sources` | list[str] | `["ci_logs", "sentry", "test_output"]` | Failure log sources |

## supervision

### supervision.gates[]

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | string | **required** | Unique gate identifier |
| `trigger` | string | **required** | When the gate activates |
| `type` | enum | `"human_approval"` | `human_approval`, `confidence_gate`, `time_gate`, `branch_gate` |
| `notify` | list[str] | `[]` | Notification channels: `slack`, `email`, `github` |
| `timeout_hours` | int | `24` | Hours before timeout action |
| `on_timeout` | enum | `"block"` | `block`, `auto_approve`, `escalate` |
| `threshold` | float | `null` | Confidence threshold (for `confidence_gate`) |
| `required_approvers` | int | `0` | Number of required approvers |

### supervision.audit_log

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `audit_log` | string | `".devlution/audit.jsonl"` | Path to audit log file |

## integrations

### integrations.github

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `true` | Enable GitHub integration |
| `auto_label_prs` | bool | `true` | Auto-apply labels to PRs |
| `pr_template` | string | `".github/pull_request_template.md"` | PR body template path |
| `labels.ai_generated` | string | `"ai-generated"` | Label for AI-generated PRs |
| `labels.needs_review` | string | `"needs-review"` | Label for PRs needing review |

### integrations.slack

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable Slack integration |
| `channel` | string | `"#dev-pipeline"` | Notification channel |

### integrations.sentry

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable Sentry integration |
| `project_slug` | string | `""` | Sentry project slug |
| `auto_create_issues` | bool | `true` | Auto-create issues from alerts |

### integrations.jira

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | `false` | Enable Jira integration |

## pipeline

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `flow` | list[str] | `[]` | Default pipeline flow |
| `triggers` | list | `[]` | Trigger-specific flow overrides |

### pipeline.triggers[]

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `on` | string | **required** | Trigger type: `github_issue`, `ci_failure`, `sentry_alert`, `schedule`, `manual` |
| `label` | string | `null` | Issue label filter (for `github_issue`) |
| `cron` | string | `null` | Cron expression (for `schedule`) |
| `flow` | list[str] | `[]` | Pipeline flow for this trigger |
