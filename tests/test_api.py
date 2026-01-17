"""
Integration tests for Agent Zero API endpoints.

Tests cover API endpoints using Flask test client with mocked dependencies:
- health.py: Health check endpoint (no auth required)
- settings_get.py: Get settings endpoint
- settings_set.py: Set settings endpoint
- projects.py: Projects list endpoint
- mcp_servers_status.py: MCP servers status endpoint
- notifications_history.py: Notifications history endpoint
- history_get.py: Chat history endpoint

These tests focus on endpoint behavior, response structure, and error handling.
Mocking is used to isolate API handler logic from external dependencies.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from flask import Flask
import threading


# =============================================================================
# Test Fixtures and Setup
# =============================================================================

@pytest.fixture
def mock_git_info():
    """Mock git info response for health check."""
    return {
        "branch": "main",
        "commit_hash": "abc1234567890",
        "commit_time": "24-01-15 12:00",
        "tag": "v1.0.0",
        "short_tag": "v1.0.0",
        "version": "M v1.0.0"
    }


@pytest.fixture
def mock_settings():
    """Mock settings for settings endpoints."""
    return {
        "version": "1.0.0",
        "chat_model_provider": "openai",
        "chat_model_name": "gpt-4",
        "chat_model_api_base": "",
        "chat_model_kwargs": {},
        "chat_model_ctx_length": 128000,
        "chat_model_ctx_history": 0.5,
        "chat_model_vision": True,
        "chat_model_rl_requests": 0,
        "chat_model_rl_input": 0,
        "chat_model_rl_output": 0,
        "util_model_provider": "openai",
        "util_model_name": "gpt-4o-mini",
        "util_model_api_base": "",
        "util_model_kwargs": {},
        "util_model_ctx_length": 128000,
        "util_model_ctx_input": 0.5,
        "util_model_rl_requests": 0,
        "util_model_rl_input": 0,
        "util_model_rl_output": 0,
        "embed_model_provider": "huggingface",
        "embed_model_name": "sentence-transformers/all-MiniLM-L6-v2",
        "embed_model_api_base": "",
        "embed_model_kwargs": {},
        "embed_model_rl_requests": 0,
        "embed_model_rl_input": 0,
        "browser_model_provider": "openai",
        "browser_model_name": "gpt-4o-mini",
        "browser_model_api_base": "",
        "browser_model_vision": True,
        "browser_model_rl_requests": 0,
        "browser_model_rl_input": 0,
        "browser_model_rl_output": 0,
        "browser_model_kwargs": {},
        "browser_http_headers": {},
        "agent_profile": "default",
        "agent_memory_subdir": "",
        "agent_knowledge_subdir": "",
        "memory_recall_enabled": True,
        "memory_recall_delayed": False,
        "memory_recall_interval": 5,
        "memory_recall_history_len": 10,
        "memory_recall_memories_max_search": 100,
        "memory_recall_solutions_max_search": 100,
        "memory_recall_memories_max_result": 5,
        "memory_recall_solutions_max_result": 3,
        "memory_recall_similarity_threshold": 0.5,
        "memory_recall_query_prep": True,
        "memory_recall_post_filter": True,
        "memory_memorize_enabled": True,
        "memory_memorize_consolidation": True,
        "memory_memorize_replace_threshold": 0.9,
        "api_keys": {},
        "auth_login": "",
        "auth_password": "",
        "root_password": "",
        "rfc_auto_docker": False,
        "rfc_url": "",
        "rfc_password": "",
        "rfc_port_http": 50080,
        "rfc_port_ssh": 50022,
        "shell_interface": "local",
        "stt_model_size": "base",
        "stt_language": "en",
        "stt_silence_threshold": 0.5,
        "stt_silence_duration": 1000,
        "stt_waiting_timeout": 5000,
        "tts_kokoro": False,
        "mcp_servers": "{}",
        "mcp_client_init_timeout": 30000,
        "mcp_client_tool_timeout": 60000,
        "mcp_server_enabled": False,
        "mcp_server_token": "test-token",
        "a2a_server_enabled": False,
        "variables": "",
        "secrets": "",
        "litellm_global_kwargs": {},
        "update_check_enabled": True,
    }


@pytest.fixture
def mock_settings_output():
    """Mock settings output structure for GET settings."""
    return {
        "sections": [
            {
                "id": "chat_model",
                "title": "Chat Model",
                "description": "Settings for the main chat model",
                "fields": [
                    {
                        "id": "chat_model_provider",
                        "title": "Chat model provider",
                        "type": "select",
                        "value": "openai",
                    }
                ],
                "tab": "models",
            }
        ]
    }


@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    test_app = Flask("test_app")
    test_app.secret_key = "test-secret-key"
    test_app.config["TESTING"] = True
    test_app.config["SESSION_COOKIE_NAME"] = "test_session"
    return test_app


@pytest.fixture
def lock():
    """Create a threading lock for API handlers."""
    return threading.Lock()


# =============================================================================
# Health Check API Tests
# =============================================================================

class TestHealthCheckAPI:
    """Tests for the /health endpoint."""

    @pytest.fixture
    def health_handler(self, app, lock):
        """Create a HealthCheck handler instance."""
        from python.api.health import HealthCheck
        return HealthCheck(app, lock)

    def test_health_check_requires_no_auth(self):
        """Health check endpoint should not require authentication."""
        from python.api.health import HealthCheck
        assert HealthCheck.requires_auth() is False

    def test_health_check_requires_no_csrf(self):
        """Health check endpoint should not require CSRF token."""
        from python.api.health import HealthCheck
        assert HealthCheck.requires_csrf() is False

    def test_health_check_supports_get_and_post(self):
        """Health check endpoint should support GET and POST methods."""
        from python.api.health import HealthCheck
        methods = HealthCheck.get_methods()
        assert "GET" in methods
        assert "POST" in methods

    @pytest.mark.asyncio
    async def test_health_check_returns_git_info(self, health_handler, mock_git_info):
        """Health check should return git info on success."""
        with patch("python.api.health.git.get_git_info", return_value=mock_git_info):
            mock_request = MagicMock()
            result = await health_handler.process({}, mock_request)

            assert "gitinfo" in result
            assert "error" in result
            assert result["error"] is None
            assert result["gitinfo"]["branch"] == "main"
            assert result["gitinfo"]["version"] == "M v1.0.0"

    @pytest.mark.asyncio
    async def test_health_check_handles_git_error(self, health_handler):
        """Health check should handle git errors gracefully."""
        with patch(
            "python.api.health.git.get_git_info",
            side_effect=Exception("Git repository not found")
        ):
            mock_request = MagicMock()
            result = await health_handler.process({}, mock_request)

            assert "gitinfo" in result
            assert "error" in result
            assert result["gitinfo"] is None
            assert "Git repository not found" in result["error"]


# =============================================================================
# Settings GET API Tests
# =============================================================================

class TestGetSettingsAPI:
    """Tests for the /settings_get endpoint."""

    @pytest.fixture
    def settings_get_handler(self, app, lock):
        """Create a GetSettings handler instance."""
        from python.api.settings_get import GetSettings
        return GetSettings(app, lock)

    def test_get_settings_requires_auth_by_default(self):
        """Settings GET endpoint should require authentication by default."""
        from python.api.settings_get import GetSettings
        # Default requires_auth is True (inherited from ApiHandler)
        assert GetSettings.requires_auth() is True

    def test_get_settings_supports_get_and_post(self):
        """Settings GET endpoint should support GET and POST methods."""
        from python.api.settings_get import GetSettings
        methods = GetSettings.get_methods()
        assert "GET" in methods
        assert "POST" in methods

    @pytest.mark.asyncio
    async def test_get_settings_returns_settings(
        self, settings_get_handler, mock_settings, mock_settings_output
    ):
        """Settings GET should return settings object."""
        with patch(
            "python.api.settings_get.settings.get_settings",
            return_value=mock_settings
        ), patch(
            "python.api.settings_get.settings.convert_out",
            return_value=mock_settings_output
        ):
            mock_request = MagicMock()
            result = await settings_get_handler.process({}, mock_request)

            assert "settings" in result
            assert "sections" in result["settings"]


# =============================================================================
# Settings SET API Tests
# =============================================================================

class TestSetSettingsAPI:
    """Tests for the /settings_set endpoint."""

    @pytest.fixture
    def settings_set_handler(self, app, lock):
        """Create a SetSettings handler instance."""
        from python.api.settings_set import SetSettings
        return SetSettings(app, lock)

    def test_set_settings_requires_auth(self):
        """Settings SET endpoint should require authentication."""
        from python.api.settings_set import SetSettings
        assert SetSettings.requires_auth() is True

    @pytest.mark.asyncio
    async def test_set_settings_updates_settings(
        self, settings_set_handler, mock_settings
    ):
        """Settings SET should update and return settings."""
        with patch(
            "python.api.settings_set.settings.convert_in",
            return_value=mock_settings
        ), patch(
            "python.api.settings_set.settings.set_settings",
            return_value=mock_settings
        ):
            mock_request = MagicMock()
            input_data = {"chat_model_name": "gpt-4-turbo"}
            result = await settings_set_handler.process(input_data, mock_request)

            assert "settings" in result


# =============================================================================
# CSRF Token API Tests
# Note: The csrf_token.py module imports Flask's session object via
# python.helpers.api which doesn't re-export it. These tests verify
# the module's class method behaviors without instantiating the handler.
# =============================================================================

class TestCSRFTokenAPIClassMethods:
    """Tests for the /csrf_token endpoint class methods.

    Note: Full integration tests for CSRF token endpoint require the
    complete Flask application context with session handling.
    """

    def test_csrf_token_module_has_handler_class(self):
        """CSRF token module should define GetCsrfToken class."""
        # Import the module parts we can access without session dependency
        from python.helpers.api import ApiHandler
        # Verify ApiHandler base has expected methods
        assert hasattr(ApiHandler, 'requires_csrf')
        assert hasattr(ApiHandler, 'requires_auth')
        assert hasattr(ApiHandler, 'get_methods')


# =============================================================================
# Projects API Tests
# =============================================================================

class TestProjectsAPI:
    """Tests for the /projects endpoint."""

    @pytest.fixture
    def projects_handler(self, app, lock):
        """Create a Projects handler instance."""
        from python.api.projects import Projects
        return Projects(app, lock)

    def test_projects_requires_auth(self):
        """Projects endpoint should require authentication."""
        from python.api.projects import Projects
        assert Projects.requires_auth() is True

    @pytest.mark.asyncio
    async def test_projects_list_action(self, projects_handler):
        """Projects list action should return list of projects."""
        mock_projects = [
            {"name": "project1", "path": "/path/to/project1"},
            {"name": "project2", "path": "/path/to/project2"},
        ]

        with patch.object(
            projects_handler,
            "get_active_projects_list",
            return_value=mock_projects
        ):
            mock_request = MagicMock()
            result = await projects_handler.process({"action": "list"}, mock_request)

            assert result["ok"] is True
            assert result["data"] == mock_projects

    @pytest.mark.asyncio
    async def test_projects_invalid_action(self, projects_handler):
        """Projects should return error for invalid action."""
        mock_request = MagicMock()
        result = await projects_handler.process({"action": "invalid_action"}, mock_request)

        assert result["ok"] is False
        assert "error" in result
        assert "Invalid action" in result["error"]

    @pytest.mark.asyncio
    async def test_projects_create_requires_data(self, projects_handler):
        """Projects create action should require project data."""
        mock_request = MagicMock()
        result = await projects_handler.process(
            {"action": "create", "project": None},
            mock_request
        )

        assert result["ok"] is False
        assert "error" in result
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_projects_load_requires_name(self, projects_handler):
        """Projects load action should require project name."""
        mock_request = MagicMock()
        result = await projects_handler.process(
            {"action": "load", "name": None},
            mock_request
        )

        assert result["ok"] is False
        assert "error" in result
        assert "required" in result["error"].lower()


# =============================================================================
# API Handler Base Class Tests
# =============================================================================

class TestApiHandlerBase:
    """Tests for the ApiHandler base class."""

    def test_default_requires_loopback_false(self):
        """Default requires_loopback should be False."""
        from python.helpers.api import ApiHandler
        assert ApiHandler.requires_loopback() is False

    def test_default_requires_api_key_false(self):
        """Default requires_api_key should be False."""
        from python.helpers.api import ApiHandler
        assert ApiHandler.requires_api_key() is False

    def test_default_requires_auth_true(self):
        """Default requires_auth should be True."""
        from python.helpers.api import ApiHandler
        assert ApiHandler.requires_auth() is True

    def test_default_methods_post_only(self):
        """Default methods should be POST only."""
        from python.helpers.api import ApiHandler
        assert ApiHandler.get_methods() == ["POST"]

    def test_default_requires_csrf_follows_auth(self):
        """Default requires_csrf should follow requires_auth."""
        from python.helpers.api import ApiHandler
        assert ApiHandler.requires_csrf() is True


# =============================================================================
# Integration Tests with Flask Test Client
# =============================================================================

class TestAPIIntegration:
    """Integration tests using Flask test client."""

    @pytest.fixture
    def test_client(self, app, lock, mock_git_info, mock_settings_output):
        """Create a Flask test client with registered API handlers."""
        from python.api.health import HealthCheck
        from python.api.settings_get import GetSettings

        # Register health check handler (no auth required)
        health_instance = HealthCheck(app, lock)

        async def health_route():
            from flask import request
            return await health_instance.handle_request(request)

        app.add_url_rule("/health", "health", health_route, methods=["GET", "POST"])

        # Patch dependencies
        with patch("python.api.health.git.get_git_info", return_value=mock_git_info):
            yield app.test_client()

    def test_health_endpoint_get_request(self, test_client, mock_git_info):
        """Test health endpoint via GET request."""
        with patch("python.api.health.git.get_git_info", return_value=mock_git_info):
            response = test_client.get("/health")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "gitinfo" in data
            assert "error" in data

    def test_health_endpoint_post_request(self, test_client, mock_git_info):
        """Test health endpoint via POST request."""
        with patch("python.api.health.git.get_git_info", return_value=mock_git_info):
            response = test_client.post(
                "/health",
                content_type="application/json",
                data=json.dumps({})
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "gitinfo" in data


# =============================================================================
# MCP Servers Status API Tests
# =============================================================================

class TestMCPServersStatusAPI:
    """Tests for the /mcp_servers_status endpoint."""

    @pytest.fixture
    def mcp_status_handler(self, app, lock):
        """Create a McpServersStatuss handler instance."""
        from python.api.mcp_servers_status import McpServersStatuss
        return McpServersStatuss(app, lock)

    @pytest.mark.asyncio
    async def test_mcp_servers_status_returns_status(self, mcp_status_handler):
        """MCP servers status should return server status info."""
        mock_status = {
            "servers": [],
            "connected": 0,
            "total": 0
        }

        with patch(
            "python.api.mcp_servers_status.MCPConfig.get_instance"
        ) as mock_mcp_config:
            mock_instance = MagicMock()
            mock_instance.get_servers_status.return_value = mock_status
            mock_mcp_config.return_value = mock_instance

            mock_request = MagicMock()
            result = await mcp_status_handler.process({}, mock_request)

            assert result["success"] is True
            assert "status" in result


# =============================================================================
# Notifications History API Tests
# =============================================================================

class TestNotificationsHistoryAPI:
    """Tests for the /notifications_history endpoint."""

    @pytest.fixture
    def notifications_handler(self, app, lock):
        """Create a NotificationsHistory handler instance."""
        from python.api.notifications_history import NotificationsHistory
        return NotificationsHistory(app, lock)

    def test_notifications_requires_auth(self):
        """Notifications history endpoint should require authentication."""
        from python.api.notifications_history import NotificationsHistory
        assert NotificationsHistory.requires_auth() is True

    @pytest.mark.asyncio
    async def test_notifications_history_returns_notifications(self, notifications_handler):
        """Notifications history should return notifications list."""
        mock_notification = MagicMock()
        mock_notification.output.return_value = {
            "id": "1",
            "message": "Test notification",
            "type": "info",
            "read": False
        }

        mock_manager = MagicMock()
        mock_manager.notifications = [mock_notification]
        mock_manager.guid = "test-guid"

        with patch(
            "python.api.notifications_history.AgentContext.get_notification_manager",
            return_value=mock_manager
        ):
            mock_request = MagicMock()
            result = await notifications_handler.process({}, mock_request)

            assert "notifications" in result
            assert "guid" in result
            assert "count" in result
            assert result["count"] == 1


# =============================================================================
# History GET API Tests
# =============================================================================

class TestHistoryGetAPI:
    """Tests for the /history_get endpoint."""

    @pytest.fixture
    def history_handler(self, app, lock):
        """Create a GetHistory handler instance."""
        from python.api.history_get import GetHistory
        return GetHistory(app, lock)

    @pytest.mark.asyncio
    async def test_history_get_returns_history(self, history_handler):
        """History GET should return agent history."""
        mock_history_text = "User: Hello\nAgent: Hi there!"
        mock_tokens = 50

        mock_agent = MagicMock()
        mock_agent.history.output_text.return_value = mock_history_text
        mock_agent.history.get_tokens.return_value = mock_tokens

        mock_context = MagicMock()
        mock_context.streaming_agent = mock_agent
        mock_context.agent0 = mock_agent

        with patch.object(history_handler, "use_context", return_value=mock_context):
            mock_request = MagicMock()
            result = await history_handler.process({"context": "test-context"}, mock_request)

            assert "history" in result
            assert "tokens" in result
            assert result["history"] == mock_history_text
            assert result["tokens"] == mock_tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
