"""
Database layer for the chatbot application.

This module handles all database operations including:
- User management
- Chat management
- Message management
- Database initialization
- CRUD operations

Uses SQLite for simplicity and portability.
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import contextmanager
import config

# ============================================================================
# DATABASE CONNECTION MANAGEMENT
# ============================================================================

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    """

    conn = sqlite3.connect(config.DATABASE_PATH)

    # Allows access like:
    # row["title"]
    conn.row_factory = sqlite3.Row

    try:
        yield conn

    finally:
        conn.close()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def initialize_database():
    """
    Initialize all database tables.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        # --------------------------------------------------------------------
        # USERS TABLE
        # --------------------------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (

                user_id INTEGER PRIMARY KEY AUTOINCREMENT,

                google_id TEXT UNIQUE NOT NULL,

                email TEXT UNIQUE NOT NULL,

                name TEXT NOT NULL,

                picture_url TEXT,

                created_at TIMESTAMP NOT NULL
            )
        """)

        # --------------------------------------------------------------------
        # CHATS TABLE
        # --------------------------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (

                chat_id TEXT PRIMARY KEY,

                user_id INTEGER NOT NULL,

                title TEXT NOT NULL,

                created_at TIMESTAMP NOT NULL,

                updated_at TIMESTAMP NOT NULL,

                FOREIGN KEY (user_id)
                REFERENCES users (user_id)
                ON DELETE CASCADE
            )
        """)

        # --------------------------------------------------------------------
        # MESSAGES TABLE
        # --------------------------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (

                message_id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id TEXT NOT NULL,

                role TEXT NOT NULL,

                content TEXT NOT NULL,

                timestamp TIMESTAMP NOT NULL,

                FOREIGN KEY (chat_id)
                REFERENCES chats (chat_id)
                ON DELETE CASCADE
            )
        """)

        # --------------------------------------------------------------------
        # INDEXES
        # --------------------------------------------------------------------

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_chat_id
            ON messages (chat_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chats_user_id
            ON chats (user_id)
        """)

        conn.commit()

        print("✅ Database initialized successfully")


# ============================================================================
# USER OPERATIONS
# ============================================================================

def create_or_update_user(
    google_id: str,
    email: str,
    name: str,
    picture_url: str = None
) -> int:
    """
    Create a new user or return existing user.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("""
            SELECT user_id
            FROM users
            WHERE google_id = ?
        """, (google_id,))

        existing_user = cursor.fetchone()

        # Existing user
        if existing_user:

            # Update latest profile info
            cursor.execute("""
                UPDATE users
                SET email = ?,
                    name = ?,
                    picture_url = ?
                WHERE google_id = ?
            """, (
                email,
                name,
                picture_url,
                google_id
            ))

            conn.commit()

            return existing_user["user_id"]

        # Create new user
        cursor.execute("""
            INSERT INTO users (
                google_id,
                email,
                name,
                picture_url,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            google_id,
            email,
            name,
            picture_url,
            datetime.now()
        ))

        conn.commit()

        return cursor.lastrowid


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Get user by ID.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM users
            WHERE user_id = ?
        """, (user_id,))

        row = cursor.fetchone()

        return dict(row) if row else None


# ============================================================================
# CHAT OPERATIONS
# ============================================================================

def create_new_chat(user_id: int, title: str) -> str:
    """
    Create a new chat for a specific user.
    """

    chat_id = str(uuid.uuid4())

    now = datetime.now()

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO chats (
                chat_id,
                user_id,
                title,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            chat_id,
            user_id,
            title,
            now,
            now
        ))

        conn.commit()

    print(f"✅ Created new chat: {chat_id}")

    return chat_id


def get_all_chats(user_id: int) -> List[Dict]:
    """
    Get all chats belonging to a specific user.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                chat_id,
                title,
                created_at,
                updated_at

            FROM chats

            WHERE user_id = ?

            ORDER BY updated_at DESC
        """, (user_id,))

        rows = cursor.fetchall()

        chats = [dict(row) for row in rows]

    return chats


def get_chat_by_id(chat_id: str) -> Optional[Dict]:
    """
    Get chat by ID.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM chats
            WHERE chat_id = ?
        """, (chat_id,))

        row = cursor.fetchone()

        return dict(row) if row else None


def update_chat_timestamp(chat_id: str):
    """
    Update chat timestamp.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            UPDATE chats
            SET updated_at = ?
            WHERE chat_id = ?
        """, (
            datetime.now(),
            chat_id
        ))

        conn.commit()


def update_chat_title(chat_id: str, new_title: str):
    """
    Rename a chat.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            UPDATE chats
            SET title = ?
            WHERE chat_id = ?
        """, (
            new_title,
            chat_id
        ))

        conn.commit()


def delete_chat(chat_id: str):
    """
    Delete a chat and all messages.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM messages
            WHERE chat_id = ?
        """, (chat_id,))

        cursor.execute("""
            DELETE FROM chats
            WHERE chat_id = ?
        """, (chat_id,))

        conn.commit()

    print(f"🗑️ Deleted chat: {chat_id}")


# ============================================================================
# MESSAGE OPERATIONS
# ============================================================================

def add_message(
    chat_id: str,
    role: str,
    content: str
) -> int:
    """
    Add message to chat.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO messages (
                chat_id,
                role,
                content,
                timestamp
            )
            VALUES (?, ?, ?, ?)
        """, (
            chat_id,
            role,
            content,
            datetime.now()
        ))

        message_id = cursor.lastrowid

        conn.commit()

    # Move chat to top
    update_chat_timestamp(chat_id)

    return message_id


def get_messages_by_chat(chat_id: str) -> List[Dict]:
    """
    Get all messages for a chat.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                message_id,
                chat_id,
                role,
                content,
                timestamp

            FROM messages

            WHERE chat_id = ?

            ORDER BY timestamp ASC
        """, (chat_id,))

        rows = cursor.fetchall()

        messages = [dict(row) for row in rows]

    return messages


def get_message_count(chat_id: str) -> int:
    """
    Count messages in a chat.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as count
            FROM messages
            WHERE chat_id = ?
        """, (chat_id,))

        result = cursor.fetchone()

        return result["count"]


# ============================================================================
# DATABASE STATS
# ============================================================================

def get_database_stats() -> Dict:
    """
    Get database statistics.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        # Users
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM users
        """)

        total_users = cursor.fetchone()["count"]

        # Chats
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM chats
        """)

        total_chats = cursor.fetchone()["count"]

        # Messages
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM messages
        """)

        total_messages = cursor.fetchone()["count"]

        # Database size
        cursor.execute("""
            SELECT page_count * page_size as size
            FROM pragma_page_count(),
                 pragma_page_size()
        """)

        db_size = cursor.fetchone()["size"]

    return {
        "total_users": total_users,
        "total_chats": total_chats,
        "total_messages": total_messages,
        "database_size_bytes": db_size,
        "database_size_mb": round(
            db_size / (1024 * 1024),
            2
        )
    }


# ============================================================================
# DANGER ZONE
# ============================================================================

def clear_all_data():
    """
    ⚠️ Delete ALL data.
    """

    with get_db_connection() as conn:

        cursor = conn.cursor()

        cursor.execute("DELETE FROM messages")

        cursor.execute("DELETE FROM chats")

        cursor.execute("DELETE FROM users")

        conn.commit()

    print("🗑️ All data cleared")