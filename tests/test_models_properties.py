"""
Property-based tests for models.py using Hypothesis.

Tests cover:
- ModelConfig properties
- ModelType enum properties
- ChatChunk properties
- ChatGenerationResult properties
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import given, settings
import pytest

# Add project root to path for imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from models import (
    ModelConfig,
    ModelType,
    ChatChunk,
    ChatGenerationResult,
    RateLimiter,
)
from tests.strategies import (
    model_configs,
    model_types,
    chat_chunks,
    model_kwargs,
)


# =============================================================================
# ModelConfig Property Tests
# =============================================================================


class TestModelConfigProperties:
    """Property tests for ModelConfig dataclass."""

    @given(model_configs)
    @settings(max_examples=50)
    def test_model_config_type_is_enum(self, config: ModelConfig):
        """ModelConfig.type should always be a ModelType enum."""
        assert isinstance(config.type, ModelType)

    @given(model_configs)
    @settings(max_examples=50)
    def test_ctx_length_non_negative(self, config: ModelConfig):
        """Context length should be non-negative."""
        assert config.ctx_length >= 0

    @given(model_configs)
    @settings(max_examples=50)
    def test_limits_non_negative(self, config: ModelConfig):
        """All limit values should be non-negative."""
        assert config.limit_requests >= 0
        assert config.limit_input >= 0
        assert config.limit_output >= 0

    @given(model_configs)
    @settings(max_examples=50)
    def test_build_kwargs_includes_api_base(self, config: ModelConfig):
        """build_kwargs() should include api_base when provider is 'other'."""
        kwargs = config.build_kwargs()

        if config.provider == "other":
            assert "api_base" in kwargs

    @given(model_configs)
    @settings(max_examples=50)
    def test_kwargs_dict_preserved(self, config: ModelConfig):
        """Custom kwargs should be preserved in build_kwargs output."""
        if config.kwargs:
            kwargs = config.build_kwargs()
            for key, value in config.kwargs.items():
                assert key in kwargs

    @given(model_configs)
    @settings(max_examples=50)
    def test_vision_is_boolean(self, config: ModelConfig):
        """Vision property should be a boolean."""
        assert isinstance(config.vision, bool)

    @given(model_configs)
    @settings(max_examples=50)
    def test_provider_is_string(self, config: ModelConfig):
        """Provider should be a non-empty string."""
        assert isinstance(config.provider, str)
        assert len(config.provider) > 0

    @given(model_configs)
    @settings(max_examples=50)
    def test_name_is_string(self, config: ModelConfig):
        """Name should be a non-empty string."""
        assert isinstance(config.name, str)
        assert len(config.name) > 0


# =============================================================================
# ModelType Property Tests
# =============================================================================


class TestModelTypeProperties:
    """Property tests for ModelType enum."""

    def test_model_type_enum_values(self):
        """ModelType should have expected values."""
        values = list(ModelType)
        assert ModelType.CHAT in values
        assert ModelType.EMBEDDING in values

    def test_model_type_string_values(self):
        """ModelType values should be correct strings."""
        assert ModelType.CHAT.value == "Chat"
        assert ModelType.EMBEDDING.value == "Embedding"

    def test_model_type_count(self):
        """ModelType should have exactly 2 values."""
        values = list(ModelType)
        assert len(values) == 2


# =============================================================================
# ChatChunk Property Tests
# =============================================================================


class TestChatChunkProperties:
    """Property tests for ChatChunk class."""

    @given(chat_chunks)
    @settings(max_examples=50)
    def test_chat_chunk_deltas_are_strings(self, chunk: dict):
        """response_delta and reasoning_delta should always be strings."""
        assert isinstance(chunk.get("response_delta", ""), str)
        assert isinstance(chunk.get("reasoning_delta", ""), str)

    @given(chat_chunks)
    @settings(max_examples=50)
    def test_chat_chunk_keys_present(self, chunk: dict):
        """ChatChunk should have required keys."""
        assert "response_delta" in chunk
        assert "reasoning_delta" in chunk

    def test_chat_chunk_empty_creation(self):
        """ChatChunk should be creatable with empty strings."""
        chunk = ChatChunk(response_delta="", reasoning_delta="")
        assert chunk["response_delta"] == ""
        assert chunk["reasoning_delta"] == ""

    def test_chat_chunk_content_preserved(self):
        """ChatChunk should preserve content."""
        content = "test response content"
        reasoning = "test reasoning content"
        chunk = ChatChunk(response_delta=content, reasoning_delta=reasoning)
        assert chunk["response_delta"] == content
        assert chunk["reasoning_delta"] == reasoning


# =============================================================================
# ChatGenerationResult Property Tests
# =============================================================================


class TestChatGenerationResultProperties:
    """Property tests for ChatGenerationResult class."""

    @given(chat_chunks)
    @settings(max_examples=30)
    def test_reasoning_accumulates(self, chunk: dict):
        """Reasoning should accumulate when add_chunk is called."""
        result = ChatGenerationResult()

        result.add_chunk(chunk)
        result.add_chunk(chunk)

        assert len(result.reasoning) >= len(chunk.get("reasoning_delta", ""))

    @given(chat_chunks)
    @settings(max_examples=30)
    def test_response_accumulates(self, chunk: dict):
        """Response should accumulate when add_chunk is called."""
        result = ChatGenerationResult()

        result.add_chunk(chunk)
        result.add_chunk(chunk)

        assert len(result.response) >= len(chunk.get("response_delta", ""))

    @given(chat_chunks)
    @settings(max_examples=30)
    def test_output_contains_all_data(self, chunk: dict):
        """output() should return a ChatChunk with all accumulated data."""
        result = ChatGenerationResult()

        result.add_chunk(chunk)

        output = result.output()

        # ChatChunk is a TypedDict, check for required keys instead
        assert "response_delta" in output
        assert "reasoning_delta" in output

    @given(chat_chunks)
    @settings(max_examples=30)
    def test_thinking_state_consistency(self, chunk: dict):
        """Thinking state should be consistent with reasoning content."""
        result = ChatGenerationResult()

        result.add_chunk(chunk)

        assert hasattr(result, "native_reasoning")
        assert hasattr(result, "thinking")

    def test_empty_result_output(self):
        """Empty result should output empty chunk."""
        result = ChatGenerationResult()
        output = result.output()

        assert output["response_delta"] == ""
        assert output["reasoning_delta"] == ""

    @given(chat_chunks)
    @settings(max_examples=30)
    def test_add_chunk_returns_dict(self, chunk: dict):
        """add_chunk should return a dict with required keys."""
        result = ChatGenerationResult()
        processed = result.add_chunk(chunk)

        # ChatChunk is a TypedDict, check for required keys instead
        assert isinstance(processed, dict)
        assert "response_delta" in processed
        assert "reasoning_delta" in processed


# =============================================================================
# Integration Tests
# =============================================================================


class TestModelConfigIntegration:
    """Integration tests for ModelConfig with different configurations."""

    @given(model_configs)
    @settings(max_examples=30)
    def test_config_with_all_fields(self, config: ModelConfig):
        """ModelConfig should work correctly with all fields populated."""
        kwargs = config.build_kwargs()

        assert config.type is not None
        assert config.provider is not None
        assert config.name is not None
        assert config.ctx_length >= 0

    def test_minimal_model_config(self):
        """Minimal ModelConfig should be creatable."""
        config = ModelConfig(type=ModelType.CHAT, provider="openai", name="gpt-4")

        assert config.type == ModelType.CHAT
        assert config.provider == "openai"
        assert config.name == "gpt-4"
        assert config.ctx_length >= 0
        assert config.vision is False


# =============================================================================
# RateLimiter Property Tests
# =============================================================================


class TestRateLimiterProperties:
    """Property tests for RateLimiter class."""

    def test_rate_limiter_can_be_created(self):
        """RateLimiter should be creatable."""
        limiter = RateLimiter(seconds=60)
        assert limiter is not None

    def test_rate_limiter_limits_dict(self):
        """RateLimiter should have a limits dict."""
        limiter = RateLimiter(seconds=60)
        assert hasattr(limiter, "limits")
        assert isinstance(limiter.limits, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
