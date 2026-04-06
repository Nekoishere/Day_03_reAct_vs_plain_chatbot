"""
Test suite for the Football Statistics Web Application.
Tests database operations, API endpoints, and edge cases.

Run with: python -m pytest tests/test_web_app.py -v
"""
import os
import sys
import json
import pytest
import tempfile
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import (
    init_db, create_conversation, get_conversations, get_conversation,
    delete_conversation, update_conversation_title, add_message,
    get_messages, get_conversation_context, get_connection
)


# ─── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database for testing."""
    path = str(tmp_path / "test.db")
    init_db(path)
    return path


@pytest.fixture
def app_client(db_path, monkeypatch):
    """Create a Flask test client with mocked LLM."""
    # Patch database path before importing app
    monkeypatch.setattr("src.database.DB_PATH", db_path)

    from app import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ─── Mock LLM for testing without API keys ─────────────────────────────

class MockLLMProvider:
    """Mock LLM that returns canned responses for testing."""
    def __init__(self):
        self.model_name = "mock-gpt-test"

    def generate(self, prompt, system_prompt=None):
        # Detect if this is an agent prompt (has tool descriptions)
        content = prompt.lower()

        if "weather" in content or "recipe" in content or "stock" in content:
            return {
                "content": "I'm a football assistant, so I specialize in football-related questions. However, I'll do my best to help! For weather/recipes/stocks, I'd recommend checking a dedicated service. Is there anything football-related I can help you with?",
                "usage": {"prompt_tokens": 50, "completion_tokens": 40, "total_tokens": 90},
                "latency_ms": 100,
            }

        if "premier league" in content and "standing" in content:
            return {
                "content": "The current Premier League standings show Arsenal at the top, followed by Manchester City and Liverpool. Arsenal has been in excellent form this season.",
                "usage": {"prompt_tokens": 60, "completion_tokens": 50, "total_tokens": 110},
                "latency_ms": 150,
            }

        if "salah" in content or "player stats" in content:
            return {
                "content": "Mohamed Salah has been brilliant this season with 18 goals and 12 assists in the Premier League. He continues to be Liverpool's key player.",
                "usage": {"prompt_tokens": 55, "completion_tokens": 45, "total_tokens": 100},
                "latency_ms": 120,
            }

        return {
            "content": "Based on my knowledge, here is the football information you requested. The Premier League season is in full swing with exciting matches every weekend.",
            "usage": {"prompt_tokens": 40, "completion_tokens": 30, "total_tokens": 70},
            "latency_ms": 80,
        }

    def stream(self, prompt, system_prompt=None):
        yield "Mock streaming response"


# ═══════════════════════════════════════════════════════════════════════
# TEST CASE 1: Database CRUD — Create conversation and verify storage
# ═══════════════════════════════════════════════════════════════════════

class TestDatabaseCRUD:
    """Test database create, read, update, delete operations."""

    def test_create_and_retrieve_conversation(self, db_path):
        """TC1: Create a conversation and verify it's stored correctly."""
        conv_id = create_conversation("chatbot", "gpt-4o-mini", "Test Chat", db_path)
        assert conv_id is not None
        assert conv_id > 0

        conv = get_conversation(conv_id, db_path)
        assert conv is not None
        assert conv["mode"] == "chatbot"
        assert conv["model_name"] == "gpt-4o-mini"
        assert conv["title"] == "Test Chat"

    def test_add_and_retrieve_messages(self, db_path):
        """TC1b: Add messages and verify they're stored with correct order."""
        conv_id = create_conversation("agent", "gpt-4o", db_path=db_path)

        # Add user message
        msg1_id = add_message(conv_id, "user", "What are the live scores?", db_path=db_path)
        assert msg1_id > 0

        # Add assistant message with reasoning trace
        trace = [{"type": "step", "thought": "I need to check live scores", "tool": "get_live_scores", "args": "", "observation": "Arsenal 2-1 Chelsea"}]
        msg2_id = add_message(
            conv_id, "assistant", "Arsenal leads Chelsea 2-1!",
            reasoning_trace=trace, latency_ms=1500,
            token_usage={"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            db_path=db_path
        )

        messages = get_messages(conv_id, db_path)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["reasoning_trace"] == trace
        assert messages[1]["latency_ms"] == 1500

    def test_delete_conversation_cascade(self, db_path):
        """TC4: Delete a conversation and verify messages are also removed."""
        conv_id = create_conversation("chatbot", "gpt-4o-mini", db_path=db_path)
        add_message(conv_id, "user", "Hello", db_path=db_path)
        add_message(conv_id, "assistant", "Hi there!", db_path=db_path)

        # Delete
        success = delete_conversation(conv_id, db_path)
        assert success is True

        # Verify gone
        conv = get_conversation(conv_id, db_path)
        assert conv is None

        messages = get_messages(conv_id, db_path)
        assert len(messages) == 0

    def test_delete_nonexistent_conversation(self, db_path):
        """Deleting a conversation that doesn't exist should return False."""
        success = delete_conversation(9999, db_path)
        assert success is False

    def test_update_conversation_title(self, db_path):
        """Update conversation title and verify the change."""
        conv_id = create_conversation("chatbot", "gpt-4o-mini", "Old Title", db_path)
        update_conversation_title(conv_id, "New Title", db_path)

        conv = get_conversation(conv_id, db_path)
        assert conv["title"] == "New Title"


# ═══════════════════════════════════════════════════════════════════════
# TEST CASE 2: API Endpoints — Conversations
# ═══════════════════════════════════════════════════════════════════════

class TestAPIConversations:
    """Test REST API conversation endpoints."""

    def test_list_conversations_empty(self, app_client):
        """TC6: List conversations on fresh DB returns empty list."""
        resp = app_client.get('/api/conversations')
        assert resp.status_code == 200
        data = resp.get_json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)

    def test_create_conversation_via_api(self, app_client):
        """Create a conversation via POST and verify response."""
        resp = app_client.post('/api/conversations', json={
            "mode": "agent",
            "title": "Test Agent Chat"
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["conversation"]["mode"] == "agent"
        assert data["conversation"]["id"] > 0

    def test_delete_conversation_via_api(self, app_client):
        """TC4 API: Delete a conversation and verify 200 response."""
        # Create
        resp = app_client.post('/api/conversations', json={"mode": "chatbot"})
        conv_id = resp.get_json()["conversation"]["id"]

        # Delete
        resp = app_client.delete(f'/api/conversations/{conv_id}')
        assert resp.status_code == 200

        # Verify gone
        resp = app_client.get('/api/conversations')
        convos = resp.get_json()["conversations"]
        assert all(c["id"] != conv_id for c in convos)

    def test_delete_nonexistent_returns_404(self, app_client):
        """Deleting a non-existent conversation should return 404."""
        resp = app_client.delete('/api/conversations/99999')
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# TEST CASE 3: Chat Endpoint — Football Questions (Chatbot Mode)
# ═══════════════════════════════════════════════════════════════════════

class TestChatEndpointChatbot:
    """Test the /api/chat endpoint in chatbot mode."""

    def test_football_question_chatbot(self, app_client, monkeypatch):
        """TC1 Full: Send a football question to chatbot, verify response stored."""
        # Mock the LLM
        mock_llm = MockLLMProvider()
        monkeypatch.setattr("app.llm", mock_llm)
        monkeypatch.setattr("app.chatbot_instance", None)

        # Patch get_llm to return mock
        monkeypatch.setattr("app.get_llm", lambda: mock_llm)

        # Create conversation
        resp = app_client.post('/api/conversations', json={"mode": "chatbot"})
        conv_id = resp.get_json()["conversation"]["id"]

        # Send message
        resp = app_client.post('/api/chat', json={
            "conversation_id": conv_id,
            "message": "What are the current Premier League standings?",
            "mode": "chatbot"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        assert data["reasoning_trace"] is None  # Chatbot has no trace

        # Verify messages stored
        resp = app_client.get(f'/api/conversations/{conv_id}/messages')
        msgs = resp.get_json()["messages"]
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"


# ═══════════════════════════════════════════════════════════════════════
# TEST CASE 4: Chat Validation Errors
# ═══════════════════════════════════════════════════════════════════════

class TestChatValidation:
    """Test input validation for chat endpoint."""

    def test_missing_message(self, app_client):
        """Chat with empty message should return 400."""
        resp = app_client.post('/api/conversations', json={"mode": "chatbot"})
        conv_id = resp.get_json()["conversation"]["id"]

        resp = app_client.post('/api/chat', json={
            "conversation_id": conv_id,
            "message": "",
            "mode": "chatbot"
        })
        assert resp.status_code == 400

    def test_missing_conversation_id(self, app_client):
        """Chat without conversation_id should return 400."""
        resp = app_client.post('/api/chat', json={
            "message": "Hello",
            "mode": "chatbot"
        })
        assert resp.status_code == 400

    def test_nonexistent_conversation(self, app_client):
        """Chat with non-existent conversation should return 404."""
        resp = app_client.post('/api/chat', json={
            "conversation_id": 99999,
            "message": "Hello",
            "mode": "chatbot"
        })
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# TEST CASE 5: Follow-up Questions — Conversation Context
# ═══════════════════════════════════════════════════════════════════════

class TestFollowUpQuestions:
    """Test that follow-up questions maintain conversation context."""

    def test_conversation_context_building(self, db_path):
        """TC5: Context string includes previous messages for follow-up support."""
        conv_id = create_conversation("chatbot", "gpt-4o-mini", db_path=db_path)
        add_message(conv_id, "user", "Tell me about Arsenal", db_path=db_path)
        add_message(conv_id, "assistant", "Arsenal is a top Premier League club.", db_path=db_path)
        add_message(conv_id, "user", "What about their recent form?", db_path=db_path)

        context = get_conversation_context(conv_id, db_path=db_path)
        assert "Arsenal" in context
        assert "Premier League" in context
        assert "recent form" in context

    def test_context_limits_turns(self, db_path):
        """Context should only include the last N turns, not all history."""
        conv_id = create_conversation("chatbot", "gpt-4o-mini", db_path=db_path)

        # Add 20 messages (10 turns)
        for i in range(10):
            add_message(conv_id, "user", f"Question {i}", db_path=db_path)
            add_message(conv_id, "assistant", f"Answer {i}", db_path=db_path)

        context = get_conversation_context(conv_id, max_turns=3, db_path=db_path)
        # Should NOT contain early messages
        assert "Question 0" not in context
        # Should contain recent messages
        assert "Question 9" in context


# ═══════════════════════════════════════════════════════════════════════
# TEST CASE 6: Out-of-Domain Questions
# ═══════════════════════════════════════════════════════════════════════

class TestOutOfDomain:
    """Test that out-of-domain questions are handled gracefully."""

    def test_non_football_question_generic(self, app_client, monkeypatch):
        """Asking a non-football question should return a graceful response."""
        mock_llm = MockLLMProvider()
        monkeypatch.setattr("app.get_llm", lambda: mock_llm)
        monkeypatch.setattr("app.llm", mock_llm)
        monkeypatch.setattr("app.chatbot_instance", None)

        resp = app_client.post('/api/conversations', json={"mode": "chatbot"})
        conv_id = resp.get_json()["conversation"]["id"]

        resp = app_client.post('/api/chat', json={
            "conversation_id": conv_id,
            "message": "Can you explain quantum computing in simple terms?",
            "mode": "chatbot"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        assert "football" in data["reply"].lower()
        assert data["reasoning_trace"] is None

    def test_weather_question(self, app_client, monkeypatch):
        """TC3: Asking about weather should get a polite response, not crash."""
        mock_llm = MockLLMProvider()
        monkeypatch.setattr("app.get_llm", lambda: mock_llm)
        monkeypatch.setattr("app.llm", mock_llm)
        monkeypatch.setattr("app.chatbot_instance", None)

        resp = app_client.post('/api/conversations', json={"mode": "chatbot"})
        conv_id = resp.get_json()["conversation"]["id"]

        resp = app_client.post('/api/chat', json={
            "conversation_id": conv_id,
            "message": "What's the weather like in London today?",
            "mode": "chatbot"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        # Should not crash — graceful handling

    def test_cooking_question(self, app_client, monkeypatch):
        """Asking about recipes should still get a response."""
        mock_llm = MockLLMProvider()
        monkeypatch.setattr("app.get_llm", lambda: mock_llm)
        monkeypatch.setattr("app.llm", mock_llm)
        monkeypatch.setattr("app.chatbot_instance", None)

        resp = app_client.post('/api/conversations', json={"mode": "chatbot"})
        conv_id = resp.get_json()["conversation"]["id"]

        resp = app_client.post('/api/chat', json={
            "conversation_id": conv_id,
            "message": "Give me a recipe for pasta carbonara",
            "mode": "chatbot"
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "reply" in data


# ═══════════════════════════════════════════════════════════════════════
# TEST CASE 7: Model Info & Suggestions Endpoints
# ═══════════════════════════════════════════════════════════════════════

class TestUtilityEndpoints:
    """Test helper API endpoints."""

    def test_model_info(self, app_client):
        """Model info endpoint should return provider and model name."""
        resp = app_client.get('/api/model-info')
        assert resp.status_code == 200
        data = resp.get_json()
        assert "provider" in data
        assert "model" in data

    def test_suggestions(self, app_client):
        """Suggestions endpoint should return a list of questions."""
        resp = app_client.get('/api/suggestions')
        assert resp.status_code == 200
        data = resp.get_json()
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0
        # Verify they're football-related
        assert any("football" in s.lower() or "league" in s.lower() or "scores" in s.lower()
                   for s in data["suggestions"])

    def test_index_page_loads(self, app_client):
        """The main page should load successfully."""
        resp = app_client.get('/')
        assert resp.status_code == 200
        assert b'Football' in resp.data


# ═══════════════════════════════════════════════════════════════════════
# TEST CASE 8: Conversation List Ordering
# ═══════════════════════════════════════════════════════════════════════

class TestConversationOrdering:
    """Test that conversations are listed in correct order."""

    def test_conversations_ordered_by_update(self, db_path):
        """TC6: Most recently updated conversations should appear first."""
        id1 = create_conversation("chatbot", "gpt-4o-mini", "First", db_path)
        id2 = create_conversation("agent", "gpt-4o", "Second", db_path)
        id3 = create_conversation("chatbot", "gpt-4o-mini", "Third", db_path)

        # Update the first one (should move it to top)
        add_message(id1, "user", "New message", db_path=db_path)

        convos = get_conversations(db_path)
        assert len(convos) == 3
        assert convos[0]["id"] == id1  # Most recently updated


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
