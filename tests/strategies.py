"""
Hypothesis strategies for property-based testing in Agent Zero.

This module provides reusable strategies for generating test data for:
- ModelType and ModelConfig
- AgentConfig
- UserMessage
- AgentContextType
- Helper strategies for paths, URLs, SSH ports, etc.
"""

from __future__ import annotations

import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from hypothesis import strategies as st

# Add project root to path for imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent import AgentContextType, AgentConfig, UserMessage
from models import ModelConfig, ModelType, ChatChunk


# =============================================================================
# ModelType Strategies
# =============================================================================

model_types = st.sampled_from(list(ModelType))


# =============================================================================
# ModelConfig Strategies
# =============================================================================

# Valid LLM providers for model configurations
model_providers = st.sampled_from(
    [
        "openai",
        "anthropic",
        "google",
        "openrouter",
        "groq",
        "azure",
        "deepseek",
        "mistral",
        "cohere",
        "huggingface",
        "ollama",
    ]
)

# Valid model name patterns
valid_model_names = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"), min_size=1, max_size=50
)

# Context length range for models
ctx_lengths = st.integers(min_value=1024, max_value=200000)

# Rate limit values
limit_values = st.integers(min_value=0, max_value=1000)

# Model configuration strategy
model_configs = st.builds(
    ModelConfig,
    type=model_types,
    provider=model_providers,
    name=valid_model_names,
    ctx_length=ctx_lengths,
    limit_requests=limit_values,
    limit_input=limit_values,
    limit_output=limit_values,
    vision=st.booleans(),
    kwargs=st.dictionaries(st.text(min_size=1), st.text()),
)


# =============================================================================
# AgentConfig Strategies
# =============================================================================

# Profile names
profile_names = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_"), max_size=50
) | st.just("")

# MCP servers string
mcp_servers = st.text(max_size=200) | st.just("")

# Knowledge subdirs
knowledge_subdirs = st.lists(st.text(min_size=1, max_size=30), min_size=1, max_size=10)

# SSH port range (valid ports)
ssh_ports = st.integers(min_value=1024, max_value=65535)

# SSH addresses (hostnames or IP addresses)
ssh_addresses = st.one_of(
    st.ip_addresses(v=4),
    st.text(min_size=7, max_size=45),  # Hostname
)

# SSH user names
ssh_users = st.text(min_size=1, max_size=50)

# Browser HTTP headers
browser_headers = st.dictionaries(st.text(min_size=1, max_size=50), st.text(min_size=1, max_size=200), max_size=10)

# Additional config dictionary
additional_dicts = st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.one_of(
        st.text(max_size=100), st.integers(), st.floats(), st.booleans(), st.lists(st.text(max_size=50), max_size=5)
    ),
    max_size=10,
)

# AgentConfig strategy with nested ModelConfig
agent_configs = st.builds(
    AgentConfig,
    chat_model=model_configs,
    utility_model=model_configs,
    embeddings_model=model_configs,
    browser_model=model_configs,
    mcp_servers=mcp_servers,
    profile=profile_names,
    knowledge_subdirs=knowledge_subdirs,
    browser_http_headers=browser_headers,
    code_exec_ssh_enabled=st.booleans(),
    code_exec_ssh_addr=ssh_addresses,
    code_exec_ssh_port=ssh_ports,
    code_exec_ssh_user=ssh_users,
    code_exec_ssh_pass=st.text(max_size=100),
    additional=additional_dicts,
)


# =============================================================================
# UserMessage Strategies
# =============================================================================

# Message content (non-empty text)
message_content = st.text(min_size=1, max_size=1000)

# Attachment paths (valid file paths)
valid_attachments = st.lists(st.text(min_size=1, max_size=500), max_size=5)

# System messages
system_messages = st.lists(st.text(min_size=1, max_size=500), max_size=3)

# UserMessage strategy
user_messages = st.builds(
    UserMessage, message=message_content, attachments=valid_attachments, system_message=system_messages
)


# =============================================================================
# AgentContextType Strategies
# =============================================================================

agent_context_types = st.sampled_from(list(AgentContextType))


# =============================================================================
# Helper Strategies
# =============================================================================


# Valid file paths
def valid_paths() -> st.SearchStrategy[str]:
    """Generate valid file paths."""
    return st.one_of(
        st.text(min_size=1, max_size=200),  # Simple filenames
        st.builds(
            lambda *parts: "/" + "/".join(parts),
            st.lists(
                st.text(
                    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_./"),
                    min_size=1,
                    max_size=50,
                ),
                min_size=1,
                max_size=5,
            ),
        ),
    )


# Valid URLs
def valid_urls() -> st.SearchStrategy[str]:
    """Generate valid URL strings."""
    protocols = st.sampled_from(["http", "https"])
    domains = st.text(min_size=1, max_size=100)
    ports = st.builds(lambda p: f":{p}" if p else "", st.integers(min_value=1, max_value=65535) | st.just(None))
    paths = st.lists(
        st.text(
            alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="-_/"), min_size=1, max_size=50
        ),
        max_size=5,
    )

    return st.builds(
        lambda protocol, domain, port, path: f"{protocol}://{domain}{port}/{'/'.join(path)}"
        if path
        else f"{protocol}://{domain}{port}",
        protocols,
        domains,
        ports,
        paths,
    )


# SSH ports
def ssh_ports_strategy() -> st.SearchStrategy[int]:
    """Generate valid SSH port numbers."""
    return st.integers(min_value=1, max_value=65535)


# Context IDs (8 character alphanumeric)
def context_ids() -> st.SearchStrategy[str]:
    """Generate valid context IDs (8 character alphanumeric)."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"),
        ),
        min_size=8,
        max_size=8,
    )


# Timestamps
def timestamps() -> st.SearchStrategy[datetime]:
    """Generate valid datetime objects."""
    return st.builds(
        datetime,
        year=st.integers(min_value=2020, max_value=2030),
        month=st.integers(min_value=1, max_value=12),
        day=st.integers(min_value=1, max_value=28),
        hour=st.integers(min_value=0, max_value=23),
        minute=st.integers(min_value=0, max_value=59),
        second=st.integers(min_value=0, max_value=59),
        tzinfo=st.just(timezone.utc),
    )


# OrderedDict strategies
def ordered_dicts(
    key_strategy: st.SearchStrategy[str] | None = None,
    value_strategy: st.SearchStrategy[Any] | None = None,
    max_size: int = 10,
) -> st.SearchStrategy[OrderedDict[str, Any]]:
    """Generate OrderedDict instances."""
    keys = key_strategy or st.text(min_size=1, max_size=50)
    values = value_strategy or st.text(max_size=100)

    return st.builds(lambda items: OrderedDict(items), st.lists(st.tuples(keys, values), min_size=0, max_size=max_size))


# Chat chunks for streaming responses
chat_chunks = st.builds(dict, response_delta=st.text(), reasoning_delta=st.text())

# Additional strategies for models
model_kwargs = st.dictionaries(
    st.text(min_size=1), st.one_of(st.text(), st.integers(), st.floats(), st.booleans()), max_size=10
)
