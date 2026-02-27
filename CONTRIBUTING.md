# Contributing to Devlution

Thank you for your interest in contributing to Devlution. This document provides guidelines and information for contributors.

---

## Development Setup

```bash
git clone https://github.com/thinkelution/devlution.git
cd devlution
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Architecture Rules

These rules are enforced across the codebase:

1. **All LLM calls go through `BaseAgent.call_llm()`** — never call the Anthropic SDK directly in agent logic
2. **All file writes go through `tools/file_editor.py`** — never use `open()` directly in agents
3. **Prompts live in `templates/prompts/`** — never hardcode prompt strings as Python strings
4. **New agents must subclass `BaseAgent`** and implement `run(input) -> output`
5. **Config is the single source of truth** — no hardcoded thresholds or model names

## Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# With verbose output
pytest -v
```

## Code Quality

```bash
# Lint
ruff check .

# Auto-fix lint issues
ruff check . --fix

# Type check
mypy devlution/
```

## Adding a New Agent

1. Create `devlution/agents/your_agent.py` subclassing `BaseAgent`
2. Set `agent_name = "your_agent"`
3. Implement `run(self, agent_input: AgentInput) -> AgentOutput`
4. Create `devlution/templates/prompts/your_agent.md` with the system prompt
5. Add the agent's config model in `devlution/config.py`
6. Wire it into the graph in `devlution/orchestrator/graph.py`
7. Add unit tests in `tests/unit/test_your_agent.py`

## Adding a New Integration

1. Create `devlution/integrations/your_service.py`
2. Add config model in `devlution/config.py` under `IntegrationsConfig`
3. Add environment variable documentation in README.md
4. Write tests that mock the external API

## Prompt Versioning

Agent prompts are versioned Markdown files. When modifying prompts:

- Increment the version in the header comment (e.g., `v1.0` → `v1.1`)
- Document what changed and why
- Test against the fixture scenarios in `tests/fixtures/`

## Commit Messages

Follow conventional commit format:

```
feat: add new capability
fix: correct a bug
test: add or update tests
docs: update documentation
refactor: restructure without behavior change
```

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass (`pytest`)
4. Ensure code is clean (`ruff check .`)
5. Submit a PR with a clear description of changes
