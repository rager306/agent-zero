# Task Completion Checklist

## Before Committing Changes

1. **Test your changes**
   ```bash
   python -m pytest tests/ -v
   ```

2. **Verify the app starts**
   ```bash
   python run_ui.py
   # Check http://localhost:5000 works
   ```

3. **Check for import errors**
   - Run the main entry point to catch missing imports

## Code Quality

- Ensure type hints are added for new functions/methods
- Follow existing naming conventions (snake_case for functions, PascalCase for classes)
- Use async/await for I/O operations
- Use dataclasses for new data structures

## When Adding New Components

### New Tool
1. Create class in `/python/tools/your_tool.py`
2. Create prompt in `/prompts/default/agent.system.tool.your_tool.md`
3. Tool automatically discovered via dynamic loading

### New Extension
1. Create in `/python/extensions/{extension_point}/`
2. Prefix with number for ordering (e.g., `_10_my_extension.py`)

### New API Endpoint
1. Create in `/python/api/your_endpoint.py`
2. Follow existing patterns for Flask routes

## Docker Testing

If changes affect Docker runtime:
```bash
docker build -f DockerfileLocal -t agent-zero-local .
docker run -p 50001:80 agent-zero-local
```
