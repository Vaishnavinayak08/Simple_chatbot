"""
Configuration file for the chatbot application.

This file contains all configuration settings including:
- Database settings
- Model configuration
- UI settings
- Authentication settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Get the directory where this config file is located
BASE_DIR = Path(__file__).parent

# Database file path - will be created in the same directory as the app
DATABASE_PATH = BASE_DIR / "chatbot.db"

# ============================================================================
# COHERE API CONFIGURATION
# ============================================================================

# Cohere model to use for chat
COHERE_MODEL = "command-r7b-12-2024"

# Get API key from environment variable
# You'll set this in .env file
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# ============================================================================
# GOOGLE OAUTH CONFIGURATION
# ============================================================================

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# OAuth redirect URI - update this based on your deployment
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8501")

# ============================================================================
# UI CONFIGURATION
# ============================================================================

# Page configuration
PAGE_TITLE = "AI Chatbot 🤖"
PAGE_ICON = "🤖"
LAYOUT = "wide"

# Sidebar settings
SIDEBAR_TITLE = "💬 Chat History"
NEW_CHAT_BUTTON_TEXT = "➕ New Chat"

# Chat settings
MAX_TITLE_LENGTH = 50  # Maximum characters for chat title
MESSAGES_PER_PAGE = 100  # How many messages to load per chat

# ============================================================================
# CHAT TITLE GENERATION
# ============================================================================

def generate_chat_title(first_message: str) -> str:
    """
    Generate a chat title from the first user message.
    
    Args:
        first_message: The first message in the chat
        
    Returns:
        A shortened title (max MAX_TITLE_LENGTH characters)
    """
    if len(first_message) <= MAX_TITLE_LENGTH:
        return first_message
    
    # Truncate and add ellipsis
    return first_message[:MAX_TITLE_LENGTH - 3] + "..."