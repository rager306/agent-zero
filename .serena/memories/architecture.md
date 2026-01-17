# Agent Zero Architecture

## Core Execution Flow
```
User → Agent 0 → Tools/Extensions → Subordinate Agents (recursive)
```

## Key Files
| File | Purpose |
|------|---------|
| `agent.py` | Core agent, AgentContext, tool execution (~922 lines) |
| `models.py` | LiteLLM wrapper for LLM providers (~919 lines) |
| `initialize.py` | AgentConfig initialization |
| `run_ui.py` | Web UI Flask server (~285 lines) |

## Directory Structure
| Directory | Purpose |
|-----------|---------|
| `/python/tools/` | Built-in tools (code_execution, memory, browser_agent, etc.) |
| `/python/extensions/` | Lifecycle hooks at 24 extension points |
| `/python/api/` | 50+ REST API endpoints |
| `/python/helpers/` | 30+ utility modules |
| `/prompts/` | System prompts (behavior defined here) |
| `/agents/` | Pre-defined agent profiles |
| `/webui/` | Frontend (vanilla HTML/CSS/JS) |

## Override Mechanism
Agent-specific components override defaults by matching filename:
- `/agents/{profile}/tools/` → `/python/tools/`
- `/agents/{profile}/extensions/` → `/python/extensions/`
- `/agents/{profile}/prompts/` → `/prompts/`

## Extension Points
Extensions hook into agent lifecycle:
- `agent_init` - agent initialization
- `before_main_llm_call` - before LLM API call
- `message_loop_start/end` - message processing boundaries
- `message_loop_prompts_before/after` - prompt processing
- `response_stream`, `reasoning_stream` - streaming handlers
- `system_prompt` - system prompt construction
- `monologue_start/end` - agent internal monologue

Extensions loaded from `/python/extensions/{extension_point}/` and executed alphabetically.
Prefix files with numbers for ordering: `_10_`, `_20_`, etc.

## Prompt System
- Main system prompt: `/prompts/default/agent.system.main.md`
- Variables: `{{var_name}}`
- Includes: `{{ include "file.md" }}`
- Dynamic loaders: Create `filename.py` alongside `filename.md`
