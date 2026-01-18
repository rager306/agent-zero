# CLAUDE.md

> **⚠️ ORCHESTRATOR MODE REQUIRED**
>
> This project uses **Orchestrator Mode** for multi-step tasks:
> - **1 command** → Execute directly
> - **2+ commands** → **DELEGATE to subagent** (never execute multiple commands yourself)
>
> See global instructions in `/root/.claude/CLAUDE.md` for full Orchestrator Mode documentation.

> **IMPORTANT: This project uses UV package manager, NOT pip!**
> - Install packages: `uv pip install <package>`
> - Sync dependencies: `uv sync`
> - Add to pyproject.toml, not requirements.txt

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Zero is an autonomous AI agent framework - a general-purpose personal assistant that uses the operating system as a tool. It features hierarchical multi-agent cooperation, persistent memory, and is fully prompt-driven with no hard-coded rails.

## Commands

### Running the Application
```bash
# Web UI (default port 5000, configurable via WEB_UI_PORT env var)
python run_ui.py

# Docker (production)
docker run -p 50001:80 agent0ai/agent-zero

# Local Docker build
docker build -f DockerfileLocal -t agent-zero-local --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .
```

### Development Setup
```bash
# Use UV package manager (NOT pip!)
uv sync
playwright install chromium
```

### Testing
```bash
# Run all tests
uv run pytest tests/

# Run only property-based tests (52 tests)
uv run pytest tests/test_agent_properties.py tests/test_models_properties.py -v

# Run with Hypothesis statistics
uv run pytest tests/test_agent_properties.py --hypothesis-show-statistics

# Run with coverage
uv run pytest tests/ --cov=python --cov-report=term-missing

# Run in parallel (uses all CPU cores)
uv run pytest tests/ -n auto
```

### Testing Strategy (Property-Based Testing)

This project uses **Hypothesis** for property-based testing in addition to traditional unit tests.

**Key Files:**
| File | Purpose |
|------|---------|
| `tests/strategies.py` | Centralized Hypothesis strategies (SINGLE SOURCE) |
| `tests/test_agent_properties.py` | Agent property-based tests (27 tests) |
| `tests/test_models_properties.py` | Models property-based tests (25 tests) |
| `docs/testing-strategy.md` | Complete testing strategy documentation |

**Strategy Pattern:**
```python
from tests.strategies import agent_configs, user_messages, model_configs

@given(agent_configs)
@settings(max_examples=50)
def test_agent_config_invariants(config):
    """Test that AgentConfig always has valid state"""
    assert config.chat_model is not None
    assert config.utility_model is not None
    assert 1 <= config.code_exec_ssh_port <= 65535
```

**Invariant Examples:**
- All 4 models (chat, utility, embeddings, browser) are present
- SSH port is in valid range (1-65535)
- message is never empty
- ctx_length >= 0 for all ModelConfig

See `docs/testing-strategy.md` for full documentation.

### Code Quality Checks
```bash
# Linting (ruff)
uv run ruff check .          # Check for issues
uv run ruff check . --fix    # Auto-fix issues

# Type checking (pyrefly - Meta's type checker)
uv run pyrefly check .

# Type checking (ty - alternative)
uv run ty check .
```

## Architecture

### Core Execution Flow
```
User → Agent 0 → Tools/Extensions → Subordinate Agents (recursive)
```

The main entry point is `run_ui.py` which initializes `AgentContext` and starts a Flask web server. Agent behavior is entirely defined by prompts in `/prompts/`.

### Key Files
| File | Purpose |
|------|---------|
| `agent.py` | Core agent implementation, AgentContext, tool execution |
| `models.py` | LiteLLM wrapper for multi-provider LLM support |
| `initialize.py` | AgentConfig initialization |
| `run_ui.py` | Web UI and Flask server |

### Directory Structure
| Directory | Purpose |
|-----------|---------|
| `/python/tools/` | Built-in tools (code_execution, memory, browser_agent, etc.) |
| `/python/extensions/` | Lifecycle hooks at 24 extension points |
| `/python/api/` | 50+ REST API endpoints |
| `/python/helpers/` | Utility modules |
| `/prompts/` | System prompts and tool instructions (behavior defined here) |
| `/agents/` | Pre-defined agent profiles with custom prompts/tools |
| `/webui/` | Frontend (vanilla HTML/CSS/JS) |

### Override Mechanism
Agent-specific components in `/agents/{profile}/` override defaults by matching filename:
- `/agents/{profile}/tools/` overrides `/python/tools/`
- `/agents/{profile}/extensions/` overrides `/python/extensions/`
- `/agents/{profile}/prompts/` overrides `/prompts/`

### Extension Points
Extensions hook into agent lifecycle at these points:
- `agent_init`, `before_main_llm_call`
- `message_loop_start`, `message_loop_end`
- `message_loop_prompts_before`, `message_loop_prompts_after`
- `response_stream`, `reasoning_stream`
- `system_prompt`, `monologue_start`, `monologue_end`

Extensions are loaded from `/python/extensions/{extension_point}/` and executed alphabetically (prefix with numbers like `_10_`, `_20_` for ordering).

### Prompt System
Prompts use Jinja-like templating:
- Variables: `{{var_name}}`
- Includes: `{{ include "file.md" }}`
- Dynamic loaders: Create `filename.py` alongside `filename.md` to generate variables at runtime

Main system prompt: `/prompts/default/agent.system.main.md`

### Tool Creation
1. Create tool class inheriting from `Tool` in `/python/tools/`
2. Add prompt file `/prompts/default/agent.system.tool.{name}.md`
3. Tools have lifecycle: `before_execution` → `execute` → `after_execution`

### Development with Docker Backend
When developing locally, configure RFC (Remote Function Call) in Settings to connect to a Docker instance for code execution. The local instance handles the framework while Docker provides the execution environment.

## Model Configuration
- Providers defined in `conf/model_providers.yaml`
- LiteLLM abstracts 20+ providers (OpenAI, Anthropic, Groq, local models, etc.)
- Settings stored in `tmp/settings.json`

## Projects
Projects provide isolated workspaces in `/a0/usr/projects/{name}/.a0proj/`:
- `instructions/` - project-specific prompts
- `memory/` - isolated memory storage
- `secrets.env` / `variables.env` - project-scoped configuration

## Versioning

**Base version: `0.9.7` (fixed, does not change)**

This fork uses extended versioning format: `0.9.7-XXX.YYY`
- `0.9.7` - base version from upstream Agent Zero (frozen)
- `XXX` - major fork iteration (increments for significant changes)
- `YYY` - minor fork iteration (increments for patches/fixes)

Example: `0.9.7-001.001` = base 0.9.7, first major iteration, first patch

---

## REMINDER: UV Package Manager

**Always use UV for Python package management in this project:**

```bash
# Install a package
uv pip install <package>

# Sync all dependencies from pyproject.toml
uv sync

# Add new dependency - edit pyproject.toml, then:
uv sync

# Inside Docker container
uv pip install <package>
uv sync --no-dev --active
```

**Never use `pip install` directly!**

---

> **⚠️ REMEMBER: ORCHESTRATOR MODE**
>
> - 1 command → Execute directly
> - 2+ commands → **DELEGATE to subagent**
>
> Full documentation: `/root/.claude/CLAUDE.md`
