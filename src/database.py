"""
Database layer for storing conversations and messages.
Uses SQLite for zero-config persistence.
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conversations.db")


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """Get a database connection with row_factory for dict-like access."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str = None):
    """Create tables if they don't exist."""
    conn = get_connection(db_path)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT 'New Conversation',
                mode TEXT NOT NULL CHECK(mode IN ('chatbot', 'agent')),
                model_name TEXT NOT NULL DEFAULT 'gpt-4o-mini',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                reasoning_trace TEXT,
                latency_ms INTEGER,
                token_usage TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id);
        """)
        conn.commit()
    finally:
        conn.close()


def create_conversation(mode: str, model_name: str, title: str = "New Conversation", db_path: str = None) -> int:
    """Create a new conversation and return its ID."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "INSERT INTO conversations (title, mode, model_name) VALUES (?, ?, ?)",
            (title, mode, model_name)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_conversations(db_path: str = None) -> List[Dict[str, Any]]:
    """Get all conversations ordered by most recent first."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_conversation(conversation_id: int, db_path: str = None) -> Optional[Dict[str, Any]]:
    """Get a single conversation by ID."""
    conn = get_connection(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_conversation(conversation_id: int, db_path: str = None) -> bool:
    """Delete a conversation and all its messages. Returns True if deleted."""
    conn = get_connection(db_path)
    try:
        cursor = conn.execute(
            "DELETE FROM conversations WHERE id = ?", (conversation_id,)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_conversation_title(conversation_id: int, title: str, db_path: str = None):
    """Update the title of a conversation."""
    conn = get_connection(db_path)
    try:
        conn.execute(
            "UPDATE conversations SET title = ?, updated_at = datetime('now') WHERE id = ?",
            (title, conversation_id)
        )
        conn.commit()
    finally:
        conn.close()


def add_message(
    conversation_id: int,
    role: str,
    content: str,
    reasoning_trace: Optional[List[Dict]] = None,
    latency_ms: Optional[int] = None,
    token_usage: Optional[Dict] = None,
    db_path: str = None
) -> int:
    """Add a message to a conversation. Returns the message ID."""
    conn = get_connection(db_path)
    try:
        trace_json = json.dumps(reasoning_trace) if reasoning_trace else None
        usage_json = json.dumps(token_usage) if token_usage else None

        cursor = conn.execute(
            """INSERT INTO messages (conversation_id, role, content, reasoning_trace, latency_ms, token_usage)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (conversation_id, role, content, trace_json, latency_ms, usage_json)
        )
        # Update conversation timestamp
        conn.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_messages(conversation_id: int, db_path: str = None) -> List[Dict[str, Any]]:
    """Get all messages for a conversation, ordered chronologically."""
    conn = get_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
            (conversation_id,)
        ).fetchall()
        results = []
        for row in rows:
            msg = dict(row)
            if msg["reasoning_trace"]:
                msg["reasoning_trace"] = json.loads(msg["reasoning_trace"])
            if msg["token_usage"]:
                msg["token_usage"] = json.loads(msg["token_usage"])
            results.append(msg)
        return results
    finally:
        conn.close()


def get_conversation_context(conversation_id: int, max_turns: int = 6, db_path: str = None) -> str:
    """
    Build conversation context string from last N turns for follow-up questions.
    This matches the format expected by BaselineChatbot and ReActAgent.
    """
    messages = get_messages(conversation_id, db_path)
    recent = messages[-(max_turns * 2):]  # Each turn = user + assistant

    context = ""
    for msg in recent:
        if msg["role"] == "user":
            context += f"User: {msg['content']}\n"
        elif msg["role"] == "assistant":
            context += f"Assistant: {msg['content']}\n"
    return context
