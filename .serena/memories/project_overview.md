# Agent Zero Project Overview

## Purpose
Agent Zero is an autonomous AI agent framework - a general-purpose personal assistant that uses the operating system as a tool. It features:
- Hierarchical multi-agent cooperation (agents can delegate to subordinate agents)
- Persistent memory system with vector search (FAISS)
- Fully prompt-driven behavior (no hard-coded rails)
- Docker-first deployment with web UI

## Tech Stack
- **Backend**: Python 3.12+, Flask (async), LiteLLM for multi-provider LLM support
- **Frontend**: Vanilla HTML/CSS/JavaScript (no framework)
- **AI/ML**: LangChain, sentence-transformers, FAISS, Whisper (STT), Kokoro (TTS)
- **Browser**: Playwright, browser-use
- **Containerization**: Docker with supervisord
- **Search**: SearXNG (integrated)

## Key Dependencies
- LiteLLM - LLM provider abstraction (20+ providers)
- Flask - Web server and API
- Playwright - Browser automation
- FAISS - Vector similarity search
- Pydantic - Data validation

## Entry Points
- `run_ui.py` - Main web UI launcher (Flask server, default port 5000)
- `agent.py` - Core agent implementation
- `models.py` - LLM model configuration
- `initialize.py` - AgentConfig initialization
