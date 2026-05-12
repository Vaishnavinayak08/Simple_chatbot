"""
Chat Manager - Business Logic Layer

This module handles the business logic for chat operations including:
- Creating and managing chat sessions
- Processing messages through the AI model
- Managing conversation history
- Interfacing between the UI and database layers
"""

import cohere
from typing import List, Dict, Optional, Tuple
import config
import database as db
from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# COHERE CLIENT INITIALIZATION
# ============================================================================

# Initialize the Cohere client with API key from environment
# This is done once when the module is imported
co = cohere.Client(config.COHERE_API_KEY)


# ============================================================================
# CHAT SESSION MANAGEMENT
# ============================================================================

class ChatSession:
    """
    Represents a single chat session.
    
    This class encapsulates all operations related to a specific chat,
    making it easier to manage state and operations.
    """
    
    def __init__(self, chat_id: Optional[str] = None):
        """
        Initialize a chat session.
        
        Args:
            chat_id: Existing chat ID, or None to create a new chat
        """
        self.chat_id = chat_id
        self._messages_cache = None  # Cache messages to avoid repeated DB queries
    
    
    def create_new(self, first_message: str) -> str:
        """
        Create a new chat session with a title based on the first message.
        
        Args:
            first_message: The first user message
            
        Returns:
            str: The new chat_id
        """
        # Generate a title from the first message
        title = config.generate_chat_title(first_message)
        
        # Create the chat in the database
        self.chat_id = db.create_new_chat(title)
        
        # Clear the cache
        self._messages_cache = None
        
        return self.chat_id
    
    
    def load_messages(self, force_refresh: bool = False) -> List[Dict]:
        """
        Load messages for this chat session.
        
        Uses caching to avoid repeated database queries unless force_refresh=True.
        
        Args:
            force_refresh: If True, bypass cache and reload from database
            
        Returns:
            List[Dict]: List of message dictionaries
        """
        if self._messages_cache is None or force_refresh:
            self._messages_cache = db.get_messages_by_chat(self.chat_id)
        
        return self._messages_cache
    
    
    def add_user_message(self, content: str):
        """
        Add a user message to the chat.
        
        Args:
            content: The message content
        """
        db.add_message(self.chat_id, role="user", content=content)
        self._messages_cache = None  # Clear cache
    
    
    def add_assistant_message(self, content: str):
        """
        Add an assistant message to the chat.
        
        Args:
            content: The message content
        """
        db.add_message(self.chat_id, role="assistant", content=content)
        self._messages_cache = None  # Clear cache
    
    
    def get_chat_info(self) -> Optional[Dict]:
        """
        Get information about this chat.
        
        Returns:
            Optional[Dict]: Chat information or None if not found
        """
        return db.get_chat_by_id(self.chat_id)
    
    
    def delete(self):
        """Delete this chat session and all its messages."""
        db.delete_chat(self.chat_id)
        self.chat_id = None
        self._messages_cache = None


# ============================================================================
# AI MESSAGE PROCESSING
# ============================================================================

def send_message_to_ai(message: str, chat_history: List[Dict]) -> str:
    """
    Send a message to the Cohere AI and get a response.
    
    This function:
    1. Formats the chat history for Cohere API
    2. Sends the message
    3. Returns the response
    
    Args:
        message: The user's message
        chat_history: Previous messages in the format from database
                      [{"role": "user", "content": "..."}, ...]
        
    Returns:
        str: The AI's response
    """
    try:
        # Format chat history for Cohere API
        formatted_history = []

        for msg in chat_history:
    
            # Convert database roles to Cohere roles
            if msg["role"] == "user":
                role = "User"
            elif msg["role"] == "assistant":
                role = "Chatbot"
            else:
                role = "System"

            formatted_history.append({
                "role": role,
                "message": msg["content"]
            })

        # Call Cohere API
        response = co.chat(
            message=message,
            model=config.COHERE_MODEL,
            chat_history=formatted_history
        )

        return response.text

    except Exception as e:
        error_message = f"Error: {str(e)}"
        print(f"❌ {error_message}")
        return f"Sorry, an error occurred: {error_message}"


# ============================================================================
# CHAT HISTORY MANAGEMENT
# ============================================================================

def get_all_chat_sessions() -> List[Dict]:
    """
    Get all chat sessions from the database.
    
    Returns:
        List[Dict]: List of chat dictionaries, ordered by most recent
    """
    return db.get_all_chats()


def get_chat_preview(chat_id: str) -> Dict:
    """
    Get a preview of a chat including message count.
    
    Args:
        chat_id: The chat to preview
        
    Returns:
        Dict: Chat information with additional preview data
    """
    chat_info = db.get_chat_by_id(chat_id)
    
    if chat_info:
        # Add message count
        chat_info['message_count'] = db.get_message_count(chat_id)
        
        # Add a preview of the last message
        messages = db.get_messages_by_chat(chat_id)
        if messages:
            last_message = messages[-1]
            # Truncate to 100 characters for preview
            preview = last_message['content'][:100]
            if len(last_message['content']) > 100:
                preview += "..."
            chat_info['last_message_preview'] = preview
        else:
            chat_info['last_message_preview'] = "No messages yet"
    
    return chat_info


# ============================================================================
# CONVERSATION FLOW
# ============================================================================

def process_user_message(chat_session: ChatSession, user_message: str) -> str:
    """
    Process a user message and get AI response.
    
    This is the main function that orchestrates a conversation turn:
    1. Save user message to database
    2. Load chat history
    3. Get AI response
    4. Save AI response to database
    
    Args:
        chat_session: The ChatSession object
        user_message: The user's message
        
    Returns:
        str: The AI's response
    """
    # Step 1: Save the user's message
    chat_session.add_user_message(user_message)
    
    # Step 2: Load the chat history (excluding the message we just added)
    # We need to format it for the AI
    all_messages = chat_session.load_messages(force_refresh=True)
    
    # The chat history for the AI should include all messages except the last one
    # (which is the message we just added and are about to send)
    chat_history_for_ai = all_messages[:-1]  # All messages except the last
    
    # Step 3: Get AI response
    ai_response = send_message_to_ai(user_message, chat_history_for_ai)
    
    # Step 4: Save the AI's response
    chat_session.add_assistant_message(ai_response)
    
    return ai_response


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def initialize_chatbot():
    """
    Initialize the chatbot system.
    
    This should be called when the app starts to ensure:
    - Database is set up
    - API keys are configured
    """
    # Initialize database
    db.initialize_database()
    
    # Verify API key is set
    if not config.COHERE_API_KEY:
        raise ValueError(
            "COHERE_API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )
    
    print("✅ Chatbot initialized successfully")


def get_system_stats() -> Dict:
    """
    Get statistics about the chatbot system.
    
    Returns:
        Dict: System statistics
    """
    db_stats = db.get_database_stats()
    
    return {
        **db_stats,
        'model': config.COHERE_MODEL,
    }