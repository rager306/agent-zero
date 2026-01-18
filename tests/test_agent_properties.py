"""
Property-based tests for agent.py classes using Hypothesis.

Tests cover:
- AgentConfig dataclass properties
- UserMessage dataclass properties
- AgentContext class properties
- LoopData class properties
"""

from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from hypothesis import given, settings
import pytest

# Add project root to path for imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent import (
    AgentContextType,
    AgentContext,
    AgentConfig,
    UserMessage,
    LoopData,
    Agent,
)
from tests.strategies import (
    agent_configs,
    user_messages,
    model_configs,
    agent_context_types,
)


# =============================================================================
# AgentConfig Property Tests
# =============================================================================


class TestAgentConfigProperties:
    """Property tests for AgentConfig dataclass."""

    @given(agent_configs)
    @settings(max_examples=50)
    def test_agent_config_always_has_required_models(self, config: AgentConfig):
        """AgentConfig should always have all 4 required models set."""
        assert config.chat_model is not None
        assert config.utility_model is not None
        assert config.embeddings_model is not None
        assert config.browser_model is not None

    @given(agent_configs)
    @settings(max_examples=50)
    def test_ssh_port_in_valid_range(self, config: AgentConfig):
        """SSH port should be in valid range 1-65535."""
        assert config.code_exec_ssh_port >= 1
        assert config.code_exec_ssh_port <= 65535

    @given(agent_configs)
    @settings(max_examples=50)
    def test_knowledge_subdirs_not_empty(self, config: AgentConfig):
        """knowledge_subdirs should not be empty."""
        assert config.knowledge_subdirs is not None
        assert len(config.knowledge_subdirs) >= 1

    @given(agent_configs)
    @settings(max_examples=50)
    def test_additional_dict_serializable(self, config: AgentConfig):
        """additional field should be serializable to JSON."""
        if config.additional:
            import json

            try:
                json.dumps(config.additional)
            except (TypeError, ValueError):
                pytest.fail("additional field is not JSON serializable")

    @given(agent_configs)
    @settings(max_examples=50)
    def test_ssh_enabled_has_addr(self, config: AgentConfig):
        """If SSH is enabled, addr should be set."""
        if config.code_exec_ssh_enabled:
            assert config.code_exec_ssh_addr is not None


# =============================================================================
# UserMessage Property Tests
# =============================================================================


class TestUserMessageProperties:
    """Property tests for UserMessage dataclass."""

    @given(user_messages)
    @settings(max_examples=50)
    def test_message_never_empty(self, msg: UserMessage):
        """Message should never be empty."""
        assert msg.message is not None
        assert len(msg.message) > 0

    @given(user_messages)
    @settings(max_examples=50)
    def test_attachments_are_strings(self, msg: UserMessage):
        """All attachments should be strings."""
        for attachment in msg.attachments:
            assert isinstance(attachment, str)

    @given(user_messages)
    @settings(max_examples=50)
    def test_system_message_list_of_strings(self, msg: UserMessage):
        """system_message should be a list of strings."""
        assert isinstance(msg.system_message, list)
        for system_msg in msg.system_message:
            assert isinstance(system_msg, str)

    @given(user_messages)
    @settings(max_examples=50)
    def test_message_max_length(self, msg: UserMessage):
        """Message should respect max length constraint."""
        assert len(msg.message) <= 1000

    @given(user_messages)
    @settings(max_examples=50)
    def test_attachments_max_count(self, msg: UserMessage):
        """Attachments should not exceed maximum count."""
        assert len(msg.attachments) <= 5

    @given(user_messages)
    @settings(max_examples=50)
    def test_system_message_max_count(self, msg: UserMessage):
        """system_message items should not exceed maximum count."""
        assert len(msg.system_message) <= 3


# =============================================================================
# AgentContext Property Tests
# =============================================================================


class TestAgentContextProperties:
    """Property tests for AgentContext class."""

    @given(model_configs)
    @settings(max_examples=30, deadline=5000)
    def test_context_id_uniqueness(self, model_config: MagicMock):
        """Context IDs should be unique when generated."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            with patch("python.helpers.log.Log"):
                config = AgentConfig(
                    chat_model=model_config,
                    utility_model=model_config,
                    embeddings_model=model_config,
                    browser_model=model_config,
                    mcp_servers="",
                )

                original_contexts = AgentContext._contexts.copy()
                AgentContext._contexts.clear()

                try:
                    ids = []
                    for _ in range(20):
                        ctx = AgentContext(config=config)
                        ids.append(ctx.id)

                    assert len(ids) == len(set(ids)), "Context IDs should be unique"
                finally:
                    AgentContext._contexts.clear()
                    AgentContext._contexts.update(original_contexts)

    @given(model_configs, agent_context_types)
    @settings(max_examples=30, deadline=5000)
    def test_context_registration(self, model_config: MagicMock, ctx_type: AgentContextType):
        """Context should be registered in _contexts after creation."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            with patch("python.helpers.log.Log"):
                config = AgentConfig(
                    chat_model=model_config,
                    utility_model=model_config,
                    embeddings_model=model_config,
                    browser_model=model_config,
                    mcp_servers="",
                )

                original_contexts = AgentContext._contexts.copy()
                AgentContext._contexts.clear()

                try:
                    ctx_id = f"test-{id(model_config)}"
                    ctx = AgentContext(config=config, id=ctx_id, type=ctx_type)

                    assert ctx_id in AgentContext._contexts
                    assert AgentContext._contexts[ctx_id] == ctx
                finally:
                    AgentContext._contexts.clear()
                    AgentContext._contexts.update(original_contexts)

    @given(model_configs)
    @settings(max_examples=20, deadline=5000)
    def test_context_data_isolation(self, model_config: MagicMock):
        """Data should be isolated between different contexts."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            with patch("python.helpers.log.Log"):
                config = AgentConfig(
                    chat_model=model_config,
                    utility_model=model_config,
                    embeddings_model=model_config,
                    browser_model=model_config,
                    mcp_servers="",
                )

                original_contexts = AgentContext._contexts.copy()
                AgentContext._counter = 0
                AgentContext._contexts.clear()

                try:
                    ctx1 = AgentContext(config=config, id="ctx1")
                    ctx2 = AgentContext(config=config, id="ctx2")

                    ctx1.set_data("key1", "value1")
                    ctx2.set_data("key2", "value2")

                    assert ctx1.get_data("key1") == "value1"
                    assert ctx1.get_data("key2") is None
                    assert ctx2.get_data("key2") == "value2"
                    assert ctx2.get_data("key1") is None
                finally:
                    AgentContext._contexts.clear()
                    AgentContext._contexts.update(original_contexts)

    @given(model_configs)
    @settings(max_examples=30, deadline=5000)
    def test_paused_state_boolean(self, model_config: MagicMock):
        """Paused state should always be a boolean."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            with patch("python.helpers.log.Log"):
                config = AgentConfig(
                    chat_model=model_config,
                    utility_model=model_config,
                    embeddings_model=model_config,
                    browser_model=model_config,
                    mcp_servers="",
                )

                original_contexts = AgentContext._contexts.copy()
                AgentContext._contexts.clear()

                try:
                    ctx1 = AgentContext(config=config, paused=True)
                    assert isinstance(ctx1.paused, bool)
                    assert ctx1.paused is True

                    ctx2 = AgentContext(config=config, paused=False)
                    assert isinstance(ctx2.paused, bool)
                    assert ctx2.paused is False

                    ctx3 = AgentContext(config=config)
                    assert isinstance(ctx3.paused, bool)
                    assert ctx3.paused is False
                finally:
                    AgentContext._contexts.clear()
                    AgentContext._contexts.update(original_contexts)


# =============================================================================
# LoopData Property Tests
# =============================================================================


class TestLoopDataProperties:
    """Property tests for LoopData class."""

    def test_iteration_starts_negative(self):
        """LoopData iteration should start at -1."""
        loop_data = LoopData()
        assert loop_data.iteration == -1

    def test_extras_are_ordered_dicts(self):
        """extras_temporary and extras_persistent should be OrderedDict."""
        loop_data = LoopData()

        assert isinstance(loop_data.extras_temporary, OrderedDict)
        assert isinstance(loop_data.extras_persistent, OrderedDict)

    def test_params_are_dicts(self):
        """params_temporary and params_persistent should be dicts."""
        loop_data = LoopData()

        assert isinstance(loop_data.params_temporary, dict)
        assert isinstance(loop_data.params_persistent, dict)

    def test_extras_order_preserved(self):
        """Extras order should be preserved when modified."""
        loop_data = LoopData()

        loop_data.extras_temporary["key1"] = "value1"
        loop_data.extras_temporary["key2"] = "value2"

        keys = list(loop_data.extras_temporary.keys())
        assert keys == ["key1", "key2"]

    def test_history_output_is_list(self):
        """history_output should be a list."""
        loop_data = LoopData()

        assert isinstance(loop_data.history_output, list)

    def test_system_is_list(self):
        """system should be a list."""
        loop_data = LoopData()

        assert isinstance(loop_data.system, list)

    def test_current_tool_can_be_none(self):
        """current_tool should default to None."""
        loop_data = LoopData()

        assert loop_data.current_tool is None

    def test_last_response_empty_string(self):
        """last_response should start as empty string."""
        loop_data = LoopData()

        assert loop_data.last_response == ""
        assert isinstance(loop_data.last_response, str)


# =============================================================================
# AgentContextType Property Tests
# =============================================================================


class TestAgentContextTypeProperties:
    """Property tests for AgentContextType enum."""

    def test_context_type_has_three_values(self):
        """AgentContextType should have exactly 3 values."""
        values = list(AgentContextType)
        assert len(values) == 3

    def test_context_type_values_are_strings(self):
        """All context type values should be strings."""
        for ctx_type in AgentContextType:
            assert isinstance(ctx_type.value, str)

    def test_context_type_expected_values(self):
        """Context types should have expected string values."""
        assert AgentContextType.USER.value == "user"
        assert AgentContextType.TASK.value == "task"
        assert AgentContextType.BACKGROUND.value == "background"


# =============================================================================
# Integration Tests
# =============================================================================


class TestAgentContextIntegration:
    """Integration tests combining multiple properties."""

    @given(model_configs, agent_context_types)
    @settings(max_examples=20, deadline=5000)
    def test_context_creation_with_all_params(self, model_config: MagicMock, ctx_type: AgentContextType):
        """Context should be created correctly with all parameters."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            with patch("python.helpers.log.Log"):
                config = AgentConfig(
                    chat_model=model_config,
                    utility_model=model_config,
                    embeddings_model=model_config,
                    browser_model=model_config,
                    mcp_servers="test-servers",
                    profile="test-profile",
                )

                original_contexts = AgentContext._contexts.copy()
                AgentContext._contexts.clear()

                try:
                    ctx = AgentContext(
                        config=config,
                        id="test-id",
                        name="Test Context",
                        type=ctx_type,
                        paused=True,
                        data={"test_key": "test_value"},
                    )

                    assert ctx.id == "test-id"
                    assert ctx.name == "Test Context"
                    assert ctx.type == ctx_type
                    assert ctx.paused is True
                    assert ctx.data.get("test_key") == "test_value"
                    assert ctx.config == config
                finally:
                    AgentContext._contexts.clear()
                    AgentContext._contexts.update(original_contexts)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
