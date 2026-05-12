"""
Database layer for the chatbot application.

This module handles all database operations including:
- Database initialization
- CRUD operations for chats and messages
- Query methods

Uses SQLite for simplicity and portability.
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
import config

# ============================================================================
# DATABASE CONNECTION MANAGEMENT
# ============================================================================

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    This ensures connections are properly closed even if errors occur.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chats")
    
    Yields:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name
    try:
        yield conn
    finally:
        conn.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def initialize_database():
    """
    Create database tables if they don't exist.
    
    This function is called when the app starts. It creates:
    1. chats table - stores chat sessions
    2. messages table - stores individual messages
    
    The function is safe to call multiple times (uses IF NOT EXISTS).
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Create chats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        
        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats (chat_id) ON DELETE CASCADE
            )
        """)
        
        # Create index on chat_id for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id 
            ON messages (chat_id)
        """)
        
        conn.commit()
        print("✅ Database initialized successfully")


# ============================================================================
# CHAT OPERATIONS
# ============================================================================

def create_new_chat(title: str) -> str:
    """
    Create a new chat session.
    
    Args:
        title: The title for the new chat
        
    Returns:
        str: The unique chat_id (UUID) for the new chat
    """
    # Generate a unique ID using UUID4
    chat_id = str(uuid.uuid4())
    now = datetime.now()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO chats (chat_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (chat_id, title, now, now))
        conn.commit()
    
    print(f"✅ Created new chat: {chat_id}")
    return chat_id


def get_all_chats() -> List[Dict]:
    """
    Retrieve all chat sessions, ordered by most recent first.
    
    Returns:
        List[Dict]: List of chat dictionaries with keys:
                    - chat_id
                    - title
                    - created_at
                    - updated_at
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chat_id, title, created_at, updated_at
            FROM chats
            ORDER BY updated_at DESC
        """)
        
        # Convert rows to dictionaries
        rows = cursor.fetchall()
        chats = [dict(row) for row in rows]
        
    return chats


def get_chat_by_id(chat_id: str) -> Optional[Dict]:
    """
    Retrieve a specific chat by its ID.
    
    Args:
        chat_id: The unique identifier for the chat
        
    Returns:
        Optional[Dict]: Chat dictionary or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chat_id, title, created_at, updated_at
            FROM chats
            WHERE chat_id = ?
        """, (chat_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else None


def update_chat_timestamp(chat_id: str):
    """
    Update the 'updated_at' timestamp for a chat.
    
    This is called whenever a new message is added to keep
    the chat at the top of the list.
    
    Args:
        chat_id: The chat to update
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chats
            SET updated_at = ?
            WHERE chat_id = ?
        """, (datetime.now(), chat_id))
        conn.commit()


def delete_chat(chat_id: str):
    """
    Delete a chat and all its messages.
    
    Args:
        chat_id: The chat to delete
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Delete messages first (though CASCADE would handle this)
        cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        
        # Delete the chat
        cursor.execute("DELETE FROM chats WHERE chat_id = ?", (chat_id,))
        
        conn.commit()
    
    print(f"🗑️ Deleted chat: {chat_id}")


def update_chat_title(chat_id: str, new_title: str):
    """
    Update the title of a chat.
    
    Args:
        chat_id: The chat to update
        new_title: The new title
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE chats
            SET title = ?
            WHERE chat_id = ?
        """, (new_title, chat_id))
        conn.commit()


# ============================================================================
# MESSAGE OPERATIONS
# ============================================================================

def add_message(chat_id: str, role: str, content: str) -> int:
    """
    Add a message to a chat.
    
    Args:
        chat_id: The chat to add the message to
        role: Either "user" or "assistant"
        content: The message content
        
    Returns:
        int: The message_id of the newly created message
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (chat_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (chat_id, role, content, datetime.now()))
        
        message_id = cursor.lastrowid
        conn.commit()
    
    # Update the chat's timestamp to move it to the top
    update_chat_timestamp(chat_id)
    
    return message_id


def get_messages_by_chat(chat_id: str) -> List[Dict]:
    """
    Retrieve all messages for a specific chat.
    
    Args:
        chat_id: The chat to retrieve messages from
        
    Returns:
        List[Dict]: List of message dictionaries with keys:
                    - message_id
                    - chat_id
                    - role
                    - content
                    - timestamp
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, chat_id, role, content, timestamp
            FROM messages
            WHERE chat_id = ?
            ORDER BY timestamp ASC
        """, (chat_id,))
        
        rows = cursor.fetchall()
        messages = [dict(row) for row in rows]
    
    return messages


def get_message_count(chat_id: str) -> int:
    """
    Get the number of messages in a chat.
    
    Args:
        chat_id: The chat to count messages for
        
    Returns:
        int: Number of messages
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM messages
            WHERE chat_id = ?
        """, (chat_id,))
        
        result = cursor.fetchone()
        return result['count']


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_database_stats() -> Dict:
    """
    Get statistics about the database.
    
    Returns:
        Dict: Statistics including total chats, total messages, etc.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get total chats
        cursor.execute("SELECT COUNT(*) as count FROM chats")
        total_chats = cursor.fetchone()['count']
        
        # Get total messages
        cursor.execute("SELECT COUNT(*) as count FROM messages")
        total_messages = cursor.fetchone()['count']
        
        # Get database file size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()['size']
    
    return {
        'total_chats': total_chats,
        'total_messages': total_messages,
        'database_size_bytes': db_size,
        'database_size_mb': round(db_size / (1024 * 1024), 2)
    }


def clear_all_data():
    """
    ⚠️ WARNING: Delete all chats and messages from the database.
    
    This is useful for testing but dangerous in production!
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM chats")
        conn.commit()
    
    print("🗑️ All data cleared from database")