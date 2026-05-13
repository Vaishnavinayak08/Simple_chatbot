"""
Main Streamlit Application (Presentation Layer)

This file handles:
- UI rendering
- Sidebar chat history
- User interactions
- Connecting UI with business logic
"""

# ============================================================================
# IMPORTS
# ============================================================================

import streamlit as st
import config
import database as db
from dotenv import load_dotenv

load_dotenv()

from chat_manager import (
    ChatSession,
    process_user_message,
    get_all_chat_sessions,
    initialize_chatbot
)
from auth import (
    initialize_auth_session,
    is_authenticated,
    show_login_page,
    show_user_profile
)

# ============================================================================
# INITIALIZE APPLICATION
# ============================================================================

initialize_chatbot()

st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT
)
# Initialize authentication session
initialize_auth_session()
# If user is not logged in
if not is_authenticated():

    show_login_page()

    st.stop()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# Stores which chat is currently being renamed
if "editing_chat_id" not in st.session_state:
    st.session_state.editing_chat_id = None

# ============================================================================
# HANDLE URL QUERY PARAMETERS
# ============================================================================

query_params = st.query_params

# Restore chat from URL after refresh
if "chat_id" in query_params:

    url_chat_id = query_params["chat_id"]

    # Restore only if different
    if st.session_state.current_chat_id != url_chat_id:

        st.session_state.current_chat_id = url_chat_id
        st.session_state.chat_session = ChatSession(url_chat_id)

# ============================================================================
# SIDEBAR - CHAT HISTORY
# ============================================================================

with st.sidebar:

    st.title(config.SIDEBAR_TITLE)
    show_user_profile()

    # ------------------------------------------------------------------------
    # NEW CHAT BUTTON
    # ------------------------------------------------------------------------

    if st.button(config.NEW_CHAT_BUTTON_TEXT, use_container_width=True):
    
        # Reset current chat
        st.session_state.current_chat_id = None
        st.session_state.chat_session = None

        # Remove old chat_id from URL
        st.query_params.clear()

        st.rerun()

    st.divider()

    # ------------------------------------------------------------------------
    # LOAD ALL CHATS
    # ------------------------------------------------------------------------

    all_chats = get_all_chat_sessions(st.session_state.get("user_id"))

    if len(all_chats) == 0:
        st.info("No chats yet. Start a new conversation!")

    # ------------------------------------------------------------------------
    # DISPLAY CHAT BUTTONS
    # ------------------------------------------------------------------------

    for chat in all_chats:

        chat_title = chat["title"]
        chat_id = chat["chat_id"]

        # Highlight active chat
        if st.session_state.current_chat_id == chat_id:
            button_type = "primary"
        else:
            button_type = "secondary"

        col1, col2, col3 = st.columns([4, 1, 1])

        # CHAT OPEN BUTTON
        with col1:

            if st.button(
                chat_title,
                key=f"open_{chat_id}",
                use_container_width=True,
                type=button_type
            ):
                
                st.session_state.current_chat_id = chat_id
                st.session_state.chat_session = ChatSession(chat_id)
                st.query_params["chat_id"] = chat_id

                st.rerun()
        # RENAME BUTTON
        with col2:

            if st.button(
                "✏️",
                key=f"rename_{chat_id}",
                use_container_width=True
            ):

                st.session_state.editing_chat_id = chat_id

                st.rerun()

        # DELETE BUTTON
        with col3:

            if st.button(
                "🗑️",
                key=f"delete_{chat_id}",
                use_container_width=True
            ):

                # Delete from database
                db.delete_chat(chat_id)

                # If currently open chat is deleted
                if st.session_state.current_chat_id == chat_id:

                    st.session_state.current_chat_id = None
                    st.session_state.chat_session = None

                st.rerun()
                # --------------------------------------------------------------------
        # RENAME INPUT
        # --------------------------------------------------------------------

        if st.session_state.editing_chat_id == chat_id:

            new_title = st.text_input(
                "New chat title",
                value=chat_title,
                key=f"input_{chat_id}"
            )

            col_save, col_cancel = st.columns(2)

            # SAVE BUTTON
            with col_save:

                if st.button(
                    "Save",
                    key=f"save_{chat_id}",
                    use_container_width=True
                ):

                    # Avoid empty titles
                    if new_title.strip():

                        db.update_chat_title(chat_id, new_title.strip())

                    st.session_state.editing_chat_id = None

                    st.rerun()

            # CANCEL BUTTON
            with col_cancel:

                if st.button(
                    "Cancel",
                    key=f"cancel_{chat_id}",
                    use_container_width=True
                ):

                    st.session_state.editing_chat_id = None

                    st.rerun()
# ============================================================================
# MAIN CHAT AREA
# ============================================================================

st.title("🤖 AI Chatbot")

# ---------------------------------------------------------------------------
# EMPTY STATE
# ---------------------------------------------------------------------------

if st.session_state.chat_session is None:

    st.info("Start a new conversation by typing below!")

# ---------------------------------------------------------------------------
# DISPLAY EXISTING MESSAGES
# ---------------------------------------------------------------------------

if st.session_state.chat_session is not None:

    messages = st.session_state.chat_session.load_messages()

    for msg in messages:

        with st.chat_message(msg["role"]):

            st.markdown(msg["content"])

# ============================================================================
# CHAT INPUT
# ============================================================================

user_input = st.chat_input("Type your message here...")

# ============================================================================
# HANDLE USER MESSAGE
# ============================================================================

if user_input:

    # ------------------------------------------------------------------------
    # CREATE NEW CHAT IF NEEDED
    # ------------------------------------------------------------------------

    if st.session_state.chat_session is None:

        # Create new chat
        new_chat = ChatSession()

        # Create database chat entry
        chat_id = new_chat.create_new(st.session_state.user_id,user_input)

        # Save in session state
        st.session_state.current_chat_id = chat_id
        st.session_state.chat_session = new_chat

        # Save chat ID in URL
        st.query_params["chat_id"] = chat_id

    # ------------------------------------------------------------------------
    # DISPLAY USER MESSAGE
    # ------------------------------------------------------------------------

    with st.chat_message("user"):

        st.markdown(user_input)

    # ------------------------------------------------------------------------
    # GENERATE AI RESPONSE
    # ------------------------------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            ai_response = process_user_message(
                st.session_state.chat_session,
                user_input
            )

            st.markdown(ai_response)

    # ------------------------------------------------------------------------
    # REFRESH APP
    # ------------------------------------------------------------------------

    st.rerun()