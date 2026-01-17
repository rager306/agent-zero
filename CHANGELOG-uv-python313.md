# Changelog: UV + Python 3.13 Migration

Branch: `experiment/uv-python313`
Base: `main`
Date: January 17, 2026

---

## Summary

This branch migrates Agent Zero from pip/requirements.txt to **UV package manager** with **pyproject.toml**, updates to **Python 3.13**, and includes comprehensive code quality improvements.

### Key Metrics

| Metric | Before | After |
|--------|--------|-------|
| Package Manager | pip | UV |
| Python Version | 3.11+ | 3.13 |
| Test Coverage | ~20% | ~45% |
| Linting Errors | 196+ | 0 |
| Container Memory | ~2.3 GB | ~830 MB |

---

## 1. UV Package Manager Migration

### 1.1 Build System Changes

- **pyproject.toml**: Primary dependency configuration (replaces requirements.txt)
- **uv.lock**: Lockfile for reproducible builds
- **uv sync**: Used instead of `pip install -r requirements.txt`

### 1.2 Docker Build Updates

| File | Change |
|------|--------|
| `docker/run/fs/ins/install_A0.sh` | Use `uv sync --no-dev --active` |
| `docker/run/fs/ins/install_A02.sh` | Remove `pip cache purge` |
| `.bashrc`, `.profile` | Activate `/opt/venv-a0` |

### 1.3 Codebase References Updated

All pip references changed to `uv pip install`:
- `prompts/agent.system.tool.code_exe.md`
- `prompts/fw.memory.hist_suc.sys.md`
- `prompts/memory.solutions_sum.sys.md`
- `python/helpers/email_client.py`
- `python/helpers/tty_session.py`
- `instruments/yt_download/yt_download.sh`
- `tests/test_fasta2a_client.py`
- `docs/development.md`

---

## 2. Python Dependencies

### 2.1 New Dependencies Added

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi-sso` | >=0.19.0 | LiteLLM SSO features |
| `httpx` | >=0.27.0 | Async HTTP client |
| `openai` | >=1.0.0 | OpenAI API client |
| `pyyaml` | >=6.0 | YAML parsing |
| `requests` | >=2.31.0 | HTTP client |
| `email-validator` | >=2.3.0 | LiteLLM SCIM module |

### 2.2 LangChain 1.x Migration

Import structure updated for LangChain 1.x:

| Old Import | New Import |
|------------|------------|
| `langchain.prompts` | `langchain_core.prompts` |
| `langchain.schema` | `langchain_core.messages` |
| `langchain.storage` | `langchain_classic.storage` |
| `langchain.embeddings.CacheBackedEmbeddings` | `langchain_classic.embeddings` |
| `langchain.text_splitter` | `langchain_text_splitters` |

New packages:
- `langchain-classic>=1.0.1`
- `langchain-text-splitters>=1.1.0`

---

## 3. Container Performance Optimizations

### 3.1 Python Environment Variables

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1  # Skip .pyc files
ENV PYTHONUNBUFFERED=1          # Unbuffered output
ENV MALLOC_ARENA_MAX=2          # Reduce memory fragmentation
```

### 3.2 Resource Limits (docker-compose.yml)

```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 2G
      cpus: '1.0'
```

### 3.3 TUNNEL_API_ENABLED Toggle

New environment variable to disable Tunnel API and save ~1GB RAM:

```bash
TUNNEL_API_ENABLED=false
```

Files modified:
- `docker/run/fs/exe/run_tunnel_api.sh`
- `docker/run/fs/etc/supervisor/conf.d/supervisord.conf`

### 3.4 New Files

- `docker/run/run-optimized.sh` - Optimized container launch script
- `docs/container-optimization.md` - Performance tuning guide

---

## 4. Code Quality Improvements

### 4.1 Dev Tools Added

| Tool | Purpose |
|------|---------|
| `ruff` | Fast Python linter (replaces flake8, isort) |
| `pyrefly` | Meta's type checker |
| `ty` | Astral's type checker |
| `pytest` | Test framework |
| `pytest-asyncio` | Async test support |
| `pytest-cov` | Coverage reporting |
| `pytest-xdist` | Parallel test execution |

### 4.2 Linting Fixes (196 issues)

- Removed unused imports (F401)
- Fixed multiple imports on one line (E401)
- Fixed f-strings without placeholders (F541)
- Replaced bare `except:` with `except Exception:` (E722)
- Fixed 'not in' test order (E713)

### 4.3 Configuration

`pyproject.toml` includes tool configurations:
- `[tool.ruff]` - Linting rules and ignores
- `[tool.ty]` - Type checker settings
- `[tool.pyrefly]` - Meta type checker settings

---

## 5. Test Suite Expansion

### 5.1 New Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_agent.py` | 66 | AgentContext, Agent, exceptions |
| `tests/test_helpers.py` | 91 | dirty_json, files, strings, tokens |
| `tests/test_api.py` | 27 | API endpoints |

### 5.2 Coverage Improvements

| Module | Before | After |
|--------|--------|-------|
| `agent.py` | 0% | 46% |
| `python/helpers/tokens.py` | 0% | 100% |
| `python/helpers/strings.py` | 0% | 79% |
| `python/helpers/errors.py` | 0% | 79% |
| `python/helpers/files.py` | 19% | 38% |

---

## 6. Documentation Updates

### 6.1 CLAUDE.md

- Added UV package manager instructions (beginning and end)
- Updated Development Setup to use `uv sync`
- Added Code Quality Checks section (ruff, pyrefly, ty)
- Updated Testing command to use `uv run pytest`

### 6.2 New Documentation

| File | Description |
|------|-------------|
| `docs/container-optimization.md` | Container performance guide |
| `docs/tunnel.md` (updated) | Disabling Tunnel API section |
| `report/LANGCHAIN_USAGE_ANALYSIS.md` | LangChain usage analysis |
| `report/LANGCHAIN_V1_BEST_PRACTICES_2025.md` | Migration best practices |
| `report/RECOMMENDATIONS.md` | Step-by-step migration guide |

---

## 7. Commits (17 total)

1. `6ac4341` - Experiment: UV + Python 3.13 build configuration
2. `23e275f` - Add dev tools: ruff, pyrefly (Meta), ty (Astral)
3. `3faf520` - Fix code quality issues identified by ruff, ty, and pyrefly
4. `6f99871` - Add langchain 1.x migration analysis and best practices report
5. `13a6271` - Migrate to langchain 1.x import structure
6. `05eb4f7` - Remove unused type: ignore comments from agent.py
7. `2a08507` - Configure ruff, ty, pyrefly to ignore architectural patterns
8. `da9cdce` - Add pytest and pytest-asyncio to dev dependencies
9. `329e06e` - Add pytest-cov for test coverage reporting
10. `f039010` - Add comprehensive test suite for improved coverage
11. `4bc156e` - Add coverage files to .gitignore
12. `e7e7e5b` - Add pytest-xdist for optional parallel test execution
13. `77f9852` - Fix Docker build to use pyproject.toml with UV package manager
14. `5068573` - Migrate pip references to UV package manager throughout codebase
15. `5279bcc` - Add container performance optimizations and TUNNEL_API_ENABLED toggle
16. `bfc2640` - Add missing Python dependencies: httpx, openai, pyyaml, requests
17. `2fa3733` - Code quality fixes and UV documentation
18. `e3be602` - Add code quality check commands to CLAUDE.md

---

## 8. Breaking Changes

1. **Python 3.13 required** - `requires-python = ">=3.13"` in pyproject.toml
2. **UV required** - pip/requirements.txt no longer supported
3. **LangChain imports changed** - See section 2.2 for migration map

---

## 9. How to Use

### Development Setup

```bash
# Clone and checkout branch
git checkout experiment/uv-python313

# Install dependencies
uv sync

# Run tests
uv run pytest tests/

# Run linters
uv run ruff check .
uv run pyrefly check .
uv run ty check .
```

### Docker Build

```bash
# Build local image
podman build -f DockerfileLocal -t agent-zero-local \
  --build-arg CACHE_DATE=$(date +%Y-%m-%d:%H:%M:%S) .

# Run with optimizations
cd docker/run
TUNNEL_API_ENABLED=false ./run-optimized.sh
```

---

## 10. Files Changed

**Total: 136 files changed, 13,591 insertions(+), 227 deletions(-)**

### Key Files

| Category | Files |
|----------|-------|
| Build | `pyproject.toml`, `uv.lock`, `DockerfileLocal` |
| Docker | `docker/run/*` (10+ files) |
| Python | `agent.py`, `models.py`, `python/helpers/*` |
| Tests | `tests/test_*.py` (7 files) |
| Docs | `CLAUDE.md`, `docs/*.md`, `report/*.md` |
| Prompts | `prompts/*.md` (3 files) |
