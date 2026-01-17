# Suggested Commands for Agent Zero Development

## Running the Application

```bash
# Start web UI (default port 5000)
python run_ui.py

# Start with custom port
WEB_UI_PORT=8080 python run_ui.py

# Docker production run
docker run -p 50001:80 agent0ai/agent-zero

# Local Docker build
docker build -f DockerfileLocal -t agent-zero-local --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .
```

## Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements.dev.txt

# Install browser for Playwright
playwright install chromium
```

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/chunk_parser_test.py

# Run with verbose output
python -m pytest tests/ -v
```

## System Commands (Linux)

```bash
# File operations
ls -la
find . -name "*.py" -type f
grep -r "pattern" --include="*.py"

# Git
git status
git log --oneline -10
git diff

# Process management
ps aux | grep python
kill -9 <pid>
```

## VS Code Debugging
- Pre-configured in `.vscode/launch.json`
- Select "run_ui.py" configuration and press F5
- Breakpoints work in all Python files
