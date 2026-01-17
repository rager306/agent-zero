# Code Style and Conventions

## Python Style

### General
- Python 3.12+ syntax
- Type hints used (especially in dataclasses and function signatures)
- Async/await throughout for concurrent operations
- Dataclasses for data structures

### Naming
- Classes: `PascalCase` (e.g., `AgentContext`, `CodeExecution`)
- Functions/methods: `snake_case` (e.g., `call_extensions`, `get_settings`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `CODE_EXEC_TIMEOUTS`)
- Private methods: `_leading_underscore`

### Imports
- Standard library first, then third-party, then local
- Relative imports within the `python/` package
- Example:
```python
import asyncio
from dataclasses import dataclass
from python.helpers.tool import Tool, Response
from python.helpers import files, runtime
```

### Type Hints
- Use modern syntax: `list[str]` not `List[str]`
- Union types: `str | None` not `Optional[str]`
- Dict types: `dict[str, int]`

## Project Patterns

### Tool Creation
Tools inherit from `Tool` base class and implement `execute`:
```python
class MyTool(Tool):
    async def execute(self, **kwargs):
        return Response(message="result", break_loop=False)
```

### Extension Creation
Extensions inherit from `Extension` and implement `execute`:
```python
class MyExtension(Extension):
    async def execute(self, **kwargs):
        # access self.agent for agent instance
        pass
```

### Prompt Templates
- Markdown files in `/prompts/`
- Variables: `{{var_name}}`
- Includes: `{{ include "file.md" }}`
- Dynamic loaders: Python file with same name

## No Formal Linting
- No pyproject.toml, pylint, or black configuration
- Follow existing code patterns for consistency
