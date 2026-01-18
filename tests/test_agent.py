"""
Unit tests for agent.py

Tests for:
- AgentContextType enum
- AgentContext class (initialization, static methods, instance methods)
- AgentConfig dataclass
- UserMessage dataclass
- LoopData class
- Agent class (initialization, helper methods)
- Exception classes (InterventionException, HandledException)
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone
from dataclasses import fields
from collections import OrderedDict

import pytest

# Add project root to path
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
    InterventionException,
    HandledException,
)
from models import ModelConfig, ModelType
import python.helpers.log as Log

# Import strategies for reuse in parameterized tests
from tests.strategies import (
    agent_configs,
    user_messages,
    model_configs,
    agent_context_types,
)


# --- Fixtures ---


@pytest.fixture
def mock_model_config():
    """Create a mock ModelConfig for testing."""
    return ModelConfig(
        type=ModelType.CHAT,
        provider="test_provider",
        name="test_model",
        ctx_length=4096,
    )


@pytest.fixture
def mock_agent_config(mock_model_config):
    """Create a mock AgentConfig for testing."""
    return AgentConfig(
        chat_model=mock_model_config,
        utility_model=mock_model_config,
        embeddings_model=mock_model_config,
        browser_model=mock_model_config,
        mcp_servers="",
        profile="",
    )


@pytest.fixture
def clean_agent_context():
    """Ensure AgentContext._contexts is clean before and after each test."""
    # Store original state
    original_contexts = AgentContext._contexts.copy()
    original_counter = AgentContext._counter

    # Clear contexts for test
    AgentContext._contexts.clear()
    AgentContext._counter = 0

    yield

    # Restore original state
    AgentContext._contexts.clear()
    AgentContext._contexts.update(original_contexts)
    AgentContext._counter = original_counter


@pytest.fixture
def mock_log():
    """Create a mock Log instance."""
    log = MagicMock(spec=Log.Log)
    log.guid = "test-guid"
    log.updates = []
    log.logs = []
    return log


@pytest.fixture
def agent_context(mock_agent_config, clean_agent_context, mock_log):
    """Create an AgentContext instance for testing."""
    with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
        with patch("python.helpers.log.Log", return_value=mock_log):
            ctx = AgentContext(
                config=mock_agent_config,
                id="test-context-id",
                name="Test Context",
            )
            # Manually set the agent0 to avoid full initialization
            ctx.agent0 = MagicMock(spec=Agent)
            return ctx


# --- AgentContextType Tests ---


class TestAgentContextType:
    """Tests for AgentContextType enum."""

    def test_enum_values(self):
        """Test that enum has expected values."""
        assert AgentContextType.USER.value == "user"
        assert AgentContextType.TASK.value == "task"
        assert AgentContextType.BACKGROUND.value == "background"

    def test_enum_members(self):
        """Test that enum has exactly 3 members."""
        members = list(AgentContextType)
        assert len(members) == 3
        assert AgentContextType.USER in members
        assert AgentContextType.TASK in members
        assert AgentContextType.BACKGROUND in members


# --- AgentContext Tests ---


class TestAgentContextInitialization:
    """Tests for AgentContext initialization."""

    def test_basic_initialization(self, mock_agent_config, clean_agent_context):
        """Test basic AgentContext initialization."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(config=mock_agent_config)

            assert ctx.config == mock_agent_config
            assert ctx.id is not None
            assert len(ctx.id) == 8  # Generated ID length
            assert ctx.paused is False
            assert ctx.type == AgentContextType.USER
            assert ctx.data == {}
            assert ctx.output_data == {}
            assert isinstance(ctx.log, Log.Log)
            assert ctx.log.context == ctx

    def test_initialization_with_custom_id(self, mock_agent_config, clean_agent_context):
        """Test AgentContext initialization with custom ID."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(config=mock_agent_config, id="custom-id")

            assert ctx.id == "custom-id"

    def test_initialization_with_name(self, mock_agent_config, clean_agent_context):
        """Test AgentContext initialization with name."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(config=mock_agent_config, name="My Context")

            assert ctx.name == "My Context"

    def test_initialization_with_type(self, mock_agent_config, clean_agent_context):
        """Test AgentContext initialization with different types."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(config=mock_agent_config, type=AgentContextType.BACKGROUND)

            assert ctx.type == AgentContextType.BACKGROUND

    def test_initialization_with_paused(self, mock_agent_config, clean_agent_context):
        """Test AgentContext initialization with paused state."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(config=mock_agent_config, paused=True)

            assert ctx.paused is True

    def test_initialization_with_data(self, mock_agent_config, clean_agent_context):
        """Test AgentContext initialization with initial data."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            initial_data = {"key1": "value1", "key2": 42}
            ctx = AgentContext(config=mock_agent_config, data=initial_data)

            assert ctx.data == initial_data

    def test_initialization_registers_context(self, mock_agent_config, clean_agent_context):
        """Test that initialization registers context in _contexts."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(config=mock_agent_config, id="registered-id")

            assert "registered-id" in AgentContext._contexts
            assert AgentContext._contexts["registered-id"] == ctx

    def test_initialization_replaces_existing_context(self, mock_agent_config, clean_agent_context):
        """Test that initialization replaces existing context with same ID."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx1 = AgentContext(config=mock_agent_config, id="same-id")
            ctx2 = AgentContext(config=mock_agent_config, id="same-id")

            assert AgentContext._contexts["same-id"] == ctx2
            assert ctx1 != ctx2

    def test_initialization_increments_counter(self, mock_agent_config, clean_agent_context):
        """Test that initialization increments counter."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx1 = AgentContext(config=mock_agent_config)
            no1 = ctx1.no

            ctx2 = AgentContext(config=mock_agent_config)
            no2 = ctx2.no

            assert no2 == no1 + 1


class TestAgentContextStaticMethods:
    """Tests for AgentContext static methods."""

    def test_get_existing_context(self, mock_agent_config, clean_agent_context):
        """Test getting an existing context by ID."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(config=mock_agent_config, id="get-test-id")

            retrieved = AgentContext.get("get-test-id")

            assert retrieved == ctx

    def test_get_nonexistent_context(self, clean_agent_context):
        """Test getting a nonexistent context returns None."""
        retrieved = AgentContext.get("nonexistent-id")

        assert retrieved is None

    def test_first_returns_first_context(self, mock_agent_config, clean_agent_context):
        """Test first() returns the first context."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx1 = AgentContext(config=mock_agent_config, id="first-id")
            ctx2 = AgentContext(config=mock_agent_config, id="second-id")

            first = AgentContext.first()

            assert first == ctx1

    def test_first_returns_none_when_empty(self, clean_agent_context):
        """Test first() returns None when no contexts exist."""
        first = AgentContext.first()

        assert first is None

    def test_all_returns_all_contexts(self, mock_agent_config, clean_agent_context):
        """Test all() returns all contexts."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx1 = AgentContext(config=mock_agent_config, id="all-test-1")
            ctx2 = AgentContext(config=mock_agent_config, id="all-test-2")

            all_contexts = AgentContext.all()

            assert len(all_contexts) == 2
            assert ctx1 in all_contexts
            assert ctx2 in all_contexts

    def test_all_returns_empty_list_when_no_contexts(self, clean_agent_context):
        """Test all() returns empty list when no contexts exist."""
        all_contexts = AgentContext.all()

        assert all_contexts == []

    def test_generate_id_returns_8_char_string(self, clean_agent_context):
        """Test generate_id returns 8 character string."""
        generated_id = AgentContext.generate_id()

        assert len(generated_id) == 8
        assert generated_id.isalnum()

    def test_generate_id_returns_unique_ids(self, clean_agent_context):
        """Test generate_id returns unique IDs."""
        ids = [AgentContext.generate_id() for _ in range(100)]

        assert len(ids) == len(set(ids))

    def test_remove_existing_context(self, mock_agent_config, clean_agent_context):
        """Test removing an existing context."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(config=mock_agent_config, id="remove-test-id")

            removed = AgentContext.remove("remove-test-id")

            assert removed == ctx
            assert "remove-test-id" not in AgentContext._contexts

    def test_remove_nonexistent_context(self, clean_agent_context):
        """Test removing a nonexistent context returns None."""
        removed = AgentContext.remove("nonexistent-id")

        assert removed is None


class TestAgentContextDataMethods:
    """Tests for AgentContext data get/set methods."""

    def test_get_data_existing_key(self, agent_context):
        """Test getting existing data by key."""
        agent_context.data["test_key"] = "test_value"

        result = agent_context.get_data("test_key")

        assert result == "test_value"

    def test_get_data_nonexistent_key(self, agent_context):
        """Test getting nonexistent data returns None."""
        result = agent_context.get_data("nonexistent_key")

        assert result is None

    def test_set_data(self, agent_context):
        """Test setting data."""
        agent_context.set_data("new_key", "new_value")

        assert agent_context.data["new_key"] == "new_value"

    def test_set_data_overwrites_existing(self, agent_context):
        """Test setting data overwrites existing value."""
        agent_context.set_data("key", "value1")
        agent_context.set_data("key", "value2")

        assert agent_context.data["key"] == "value2"

    def test_get_output_data_existing_key(self, agent_context):
        """Test getting existing output data by key."""
        agent_context.output_data["output_key"] = {"nested": "value"}

        result = agent_context.get_output_data("output_key")

        assert result == {"nested": "value"}

    def test_get_output_data_nonexistent_key(self, agent_context):
        """Test getting nonexistent output data returns None."""
        result = agent_context.get_output_data("nonexistent_key")

        assert result is None

    def test_set_output_data(self, agent_context):
        """Test setting output data."""
        agent_context.set_output_data("output_key", [1, 2, 3])

        assert agent_context.output_data["output_key"] == [1, 2, 3]


class TestAgentContextMiscMethods:
    """Tests for miscellaneous AgentContext methods."""

    def test_get_agent_returns_streaming_agent_when_set(self, agent_context):
        """Test get_agent returns streaming_agent when set."""
        streaming_agent = MagicMock(spec=Agent)
        agent_context.streaming_agent = streaming_agent

        result = agent_context.get_agent()

        assert result == streaming_agent

    def test_get_agent_returns_agent0_when_no_streaming(self, agent_context):
        """Test get_agent returns agent0 when no streaming_agent."""
        agent_context.streaming_agent = None

        result = agent_context.get_agent()

        assert result == agent_context.agent0

    def test_kill_process_kills_task(self, agent_context):
        """Test kill_process kills the task."""
        mock_task = MagicMock()
        agent_context.task = mock_task

        agent_context.kill_process()

        mock_task.kill.assert_called_once()

    def test_kill_process_no_task(self, agent_context):
        """Test kill_process does nothing when no task."""
        agent_context.task = None

        # Should not raise
        agent_context.kill_process()


# --- AgentConfig Tests ---


class TestAgentConfig:
    """Tests for AgentConfig dataclass."""

    def test_basic_initialization(self, mock_model_config):
        """Test basic AgentConfig initialization."""
        config = AgentConfig(
            chat_model=mock_model_config,
            utility_model=mock_model_config,
            embeddings_model=mock_model_config,
            browser_model=mock_model_config,
            mcp_servers="test_servers",
        )

        assert config.chat_model == mock_model_config
        assert config.mcp_servers == "test_servers"
        assert config.profile == ""
        assert config.memory_subdir == ""
        assert config.knowledge_subdirs == ["default", "custom"]

    def test_initialization_with_profile(self, mock_model_config):
        """Test AgentConfig initialization with profile."""
        config = AgentConfig(
            chat_model=mock_model_config,
            utility_model=mock_model_config,
            embeddings_model=mock_model_config,
            browser_model=mock_model_config,
            mcp_servers="",
            profile="custom_profile",
        )

        assert config.profile == "custom_profile"

    def test_initialization_with_ssh_settings(self, mock_model_config):
        """Test AgentConfig initialization with SSH settings."""
        config = AgentConfig(
            chat_model=mock_model_config,
            utility_model=mock_model_config,
            embeddings_model=mock_model_config,
            browser_model=mock_model_config,
            mcp_servers="",
            code_exec_ssh_enabled=False,
            code_exec_ssh_addr="192.168.1.1",
            code_exec_ssh_port=22,
            code_exec_ssh_user="admin",
            code_exec_ssh_pass="secret",
        )

        assert config.code_exec_ssh_enabled is False
        assert config.code_exec_ssh_addr == "192.168.1.1"
        assert config.code_exec_ssh_port == 22
        assert config.code_exec_ssh_user == "admin"
        assert config.code_exec_ssh_pass == "secret"

    def test_initialization_with_additional_data(self, mock_model_config):
        """Test AgentConfig initialization with additional data."""
        additional = {"custom_key": "custom_value", "number": 42}
        config = AgentConfig(
            chat_model=mock_model_config,
            utility_model=mock_model_config,
            embeddings_model=mock_model_config,
            browser_model=mock_model_config,
            mcp_servers="",
            additional=additional,
        )

        assert config.additional == additional

    def test_default_values(self, mock_model_config):
        """Test AgentConfig default values."""
        config = AgentConfig(
            chat_model=mock_model_config,
            utility_model=mock_model_config,
            embeddings_model=mock_model_config,
            browser_model=mock_model_config,
            mcp_servers="",
        )

        assert config.code_exec_ssh_enabled is True
        assert config.code_exec_ssh_addr == "localhost"
        assert config.code_exec_ssh_port == 55022
        assert config.code_exec_ssh_user == "root"
        assert config.code_exec_ssh_pass == ""
        assert config.browser_http_headers == {}


# --- UserMessage Tests ---


class TestUserMessage:
    """Tests for UserMessage dataclass."""

    def test_basic_initialization(self):
        """Test basic UserMessage initialization."""
        msg = UserMessage(message="Hello, world!")

        assert msg.message == "Hello, world!"
        assert msg.attachments == []
        assert msg.system_message == []

    def test_initialization_with_attachments(self):
        """Test UserMessage initialization with attachments."""
        attachments = ["/path/to/file1.txt", "/path/to/file2.png"]
        msg = UserMessage(message="Check these files", attachments=attachments)

        assert msg.attachments == attachments

    def test_initialization_with_system_message(self):
        """Test UserMessage initialization with system message."""
        system_msgs = ["You are a helpful assistant", "Be concise"]
        msg = UserMessage(message="Hi", system_message=system_msgs)

        assert msg.system_message == system_msgs

    def test_full_initialization(self):
        """Test UserMessage with all parameters."""
        msg = UserMessage(
            message="Complete message",
            attachments=["file.txt"],
            system_message=["System instruction"],
        )

        assert msg.message == "Complete message"
        assert msg.attachments == ["file.txt"]
        assert msg.system_message == ["System instruction"]


# --- LoopData Tests ---


class TestLoopData:
    """Tests for LoopData class."""

    def test_default_initialization(self):
        """Test LoopData default initialization."""
        loop_data = LoopData()

        assert loop_data.iteration == -1
        assert loop_data.system == []
        assert loop_data.user_message is None
        assert loop_data.history_output == []
        assert isinstance(loop_data.extras_temporary, OrderedDict)
        assert isinstance(loop_data.extras_persistent, OrderedDict)
        assert loop_data.last_response == ""
        assert loop_data.params_temporary == {}
        assert loop_data.params_persistent == {}
        assert loop_data.current_tool is None

    def test_initialization_with_kwargs(self):
        """Test LoopData initialization with kwargs."""
        loop_data = LoopData(
            iteration=5,
            last_response="Previous response",
            current_tool="test_tool",
        )

        assert loop_data.iteration == 5
        assert loop_data.last_response == "Previous response"
        assert loop_data.current_tool == "test_tool"

    def test_initialization_with_user_message(self):
        """Test LoopData initialization with user_message."""
        mock_message = MagicMock()
        loop_data = LoopData(user_message=mock_message)

        assert loop_data.user_message == mock_message

    def test_extras_are_ordered_dicts(self):
        """Test that extras are OrderedDict instances."""
        loop_data = LoopData()

        loop_data.extras_temporary["key1"] = "value1"
        loop_data.extras_temporary["key2"] = "value2"
        loop_data.extras_persistent["a"] = 1
        loop_data.extras_persistent["b"] = 2

        # Verify order is preserved
        assert list(loop_data.extras_temporary.keys()) == ["key1", "key2"]
        assert list(loop_data.extras_persistent.keys()) == ["a", "b"]


# --- Exception Tests ---


class TestExceptions:
    """Tests for exception classes."""

    def test_intervention_exception_creation(self):
        """Test InterventionException can be created."""
        exc = InterventionException("Test intervention")

        assert str(exc) == "Test intervention"

    def test_intervention_exception_is_exception(self):
        """Test InterventionException is an Exception subclass."""
        exc = InterventionException()

        assert isinstance(exc, Exception)

    def test_handled_exception_creation(self):
        """Test HandledException can be created."""
        exc = HandledException("Test handled")

        assert str(exc) == "Test handled"

    def test_handled_exception_is_exception(self):
        """Test HandledException is an Exception subclass."""
        exc = HandledException()

        assert isinstance(exc, Exception)

    def test_intervention_exception_raise_catch(self):
        """Test InterventionException can be raised and caught."""
        with pytest.raises(InterventionException):
            raise InterventionException("Raised")

    def test_handled_exception_raise_catch(self):
        """Test HandledException can be raised and caught."""
        with pytest.raises(HandledException):
            raise HandledException("Raised")


# --- Agent Tests ---


class TestAgentInitialization:
    """Tests for Agent initialization."""

    def test_basic_initialization(self, mock_agent_config, clean_agent_context):
        """Test basic Agent initialization."""
        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            agent = Agent(number=0, config=mock_agent_config)

            assert agent.number == 0
            assert agent.config == mock_agent_config
            assert agent.agent_name == "A0"
            assert agent.intervention is None
            assert agent.data == {}
            assert agent.context is not None

    def test_initialization_with_number(self, mock_agent_config, clean_agent_context):
        """Test Agent initialization with different numbers."""
        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            agent1 = Agent(number=1, config=mock_agent_config)
            agent5 = Agent(number=5, config=mock_agent_config)

            assert agent1.agent_name == "A1"
            assert agent5.agent_name == "A5"

    def test_initialization_with_existing_context(self, mock_agent_config, clean_agent_context):
        """Test Agent initialization with existing context."""
        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            # Create context first
            ctx = AgentContext(config=mock_agent_config, id="pre-existing-ctx")

            # Create agent with that context
            agent = Agent(number=2, config=mock_agent_config, context=ctx)

            assert agent.context == ctx


class TestAgentDataMethods:
    """Tests for Agent data get/set methods."""

    def test_get_data_existing(self, mock_agent_config, clean_agent_context):
        """Test getting existing data from Agent."""
        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            agent = Agent(number=0, config=mock_agent_config)
            agent.data["test_key"] = "test_value"

            result = agent.get_data("test_key")

            assert result == "test_value"

    def test_get_data_nonexistent(self, mock_agent_config, clean_agent_context):
        """Test getting nonexistent data returns None."""
        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            agent = Agent(number=0, config=mock_agent_config)

            result = agent.get_data("nonexistent")

            assert result is None

    def test_set_data(self, mock_agent_config, clean_agent_context):
        """Test setting data on Agent."""
        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            agent = Agent(number=0, config=mock_agent_config)

            agent.set_data("new_key", {"nested": "value"})

            assert agent.data["new_key"] == {"nested": "value"}

    def test_set_data_overwrites(self, mock_agent_config, clean_agent_context):
        """Test setting data overwrites existing value."""
        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            agent = Agent(number=0, config=mock_agent_config)

            agent.set_data("key", "value1")
            agent.set_data("key", "value2")

            assert agent.data["key"] == "value2"


class TestAgentConstants:
    """Tests for Agent class constants."""

    def test_data_name_constants(self):
        """Test Agent class constants are defined correctly."""
        assert Agent.DATA_NAME_SUPERIOR == "_superior"
        assert Agent.DATA_NAME_SUBORDINATE == "_subordinate"
        assert Agent.DATA_NAME_CTX_WINDOW == "ctx_window"


class TestAgentHandleCriticalException:
    """Tests for Agent.handle_critical_exception method."""

    def test_handle_handled_exception_reraises(self, mock_agent_config, clean_agent_context):
        """Test that HandledException is re-raised."""
        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            agent = Agent(number=0, config=mock_agent_config)

            original_exc = HandledException("Already handled")

            with pytest.raises(HandledException):
                agent.handle_critical_exception(original_exc)

    def test_handle_cancelled_error_wraps_in_handled(self, mock_agent_config, clean_agent_context):
        """Test that CancelledError is wrapped in HandledException."""
        import asyncio

        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            agent = Agent(number=0, config=mock_agent_config)

            cancelled_exc = asyncio.CancelledError()

            with pytest.raises(HandledException):
                agent.handle_critical_exception(cancelled_exc)

    def test_handle_generic_exception_wraps_in_handled(self, mock_agent_config, clean_agent_context):
        """Test that generic exceptions are wrapped in HandledException."""
        with patch.object(Agent, "call_extensions", new_callable=AsyncMock):
            agent = Agent(number=0, config=mock_agent_config)

            generic_exc = ValueError("Some error")

            with pytest.raises(HandledException):
                agent.handle_critical_exception(generic_exc)


# --- Integration-like Tests ---


class TestAgentContextOutput:
    """Tests for AgentContext.output method."""

    def test_output_contains_required_fields(self, mock_agent_config, clean_agent_context):
        """Test that output contains all required fields."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(
                config=mock_agent_config,
                id="output-test-id",
                name="Output Test",
            )

            output = ctx.output()

            assert "id" in output
            assert "name" in output
            assert "created_at" in output
            assert "no" in output
            assert "log_guid" in output
            assert "log_version" in output
            assert "log_length" in output
            assert "paused" in output
            assert "last_message" in output
            assert "type" in output

    def test_output_values(self, mock_agent_config, clean_agent_context):
        """Test that output values are correct."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(
                config=mock_agent_config,
                id="output-test-id",
                name="Output Test",
                paused=True,
                type=AgentContextType.TASK,
            )

            output = ctx.output()

            assert output["id"] == "output-test-id"
            assert output["name"] == "Output Test"
            assert output["paused"] is True
            assert output["type"] == "task"

    def test_output_includes_output_data(self, mock_agent_config, clean_agent_context):
        """Test that output includes output_data fields."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(
                config=mock_agent_config,
                output_data={"custom_field": "custom_value"},
            )

            output = ctx.output()

            assert output["custom_field"] == "custom_value"


class TestAgentContextReset:
    """Tests for AgentContext.reset method."""

    def test_reset_clears_state(self, mock_agent_config, clean_agent_context):
        """Test that reset clears the context state."""
        with patch.object(Agent, "__init__", lambda self, *args, **kwargs: None):
            ctx = AgentContext(config=mock_agent_config)
            ctx.paused = True
            ctx.streaming_agent = MagicMock()
            mock_task = MagicMock()
            ctx.task = mock_task

            ctx.reset()

            assert ctx.paused is False
            assert ctx.streaming_agent is None
            mock_task.kill.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
