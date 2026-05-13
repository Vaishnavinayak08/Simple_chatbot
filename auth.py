"""
Authentication Module

This module handles:
- Google OAuth authentication
- User session management
- Login/logout functionality
"""

import streamlit as st
from streamlit_oauth import OAuth2Component
import config
import database as db
import base64
import json

# ============================================================================
# OAUTH COMPONENT INITIALIZATION
# ============================================================================

def get_oauth_component():
    """
    Initialize and return the OAuth2 component for Google authentication.
    
    Returns:
        OAuth2Component: Configured OAuth component
    """
    # Google OAuth endpoints
    AUTHORIZE_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
    REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
    
    oauth2 = OAuth2Component(
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        authorize_endpoint=AUTHORIZE_ENDPOINT,
        token_endpoint=TOKEN_ENDPOINT,
        refresh_token_endpoint=TOKEN_ENDPOINT,
        revoke_token_endpoint=REVOKE_ENDPOINT,
    )
    
    return oauth2


# ============================================================================
# USER INFO EXTRACTION
# ============================================================================

def parse_id_token(token: str) -> dict:
    """
    Parse Google ID token to extract user information.
    
    Args:
        token: JWT token from Google
        
    Returns:
        dict: User information including email, name, picture
    """
    try:
        # Split the token and get payload
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (add padding if needed)
        payload = parts[1]
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        # Decode base64
        decoded = base64.urlsafe_b64decode(payload)
        user_info = json.loads(decoded)
        
        return {
            'email': user_info.get('email', ''),
            'name': user_info.get('name', ''),
            'picture': user_info.get('picture', ''),
            'google_id': user_info.get('sub', '')
        }
    except Exception as e:
        print(f"Error parsing ID token: {e}")
        return None


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def initialize_auth_session():
    """
    Initialize authentication-related session state variables.
    """
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'token' not in st.session_state:
        st.session_state.token = None


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated.
    
    Returns:
        bool: True if user is logged in, False otherwise
    """
    return st.session_state.get('user') is not None


def get_current_user() -> dict:
    """
    Get current logged-in user information.
    
    Returns:
        dict: User information or None if not logged in
    """
    return st.session_state.get('user')


def get_current_user_id() -> str:
    """
    Get current user's database ID.
    
    Returns:
        str: User ID or None if not logged in
    """
    return st.session_state.get('user_id')


# ============================================================================
# LOGIN/LOGOUT FUNCTIONS
# ============================================================================

def handle_login(token_response: dict):
    """
    Handle successful login by storing user info and creating/updating user in DB.
    
    Args:
        token_response: Response from OAuth token endpoint
    """
    # Extract user info from ID token
    id_token = token_response.get('id_token')
    if not id_token:
        st.error("Failed to get user information")
        return
    
    user_info = parse_id_token(id_token)
    if not user_info:
        st.error("Failed to parse user information")
        return
    
    # Create or update user in database
    user_id = db.create_or_update_user(
        google_id=user_info['google_id'],
        email=user_info['email'],
        name=user_info['name'],
        picture_url=user_info['picture']
    )
    
    # Store in session
    st.session_state.user = user_info
    st.session_state.user_id = user_id
    st.session_state.token = token_response
    
    print(f"✅ User logged in: {user_info['email']}")


def handle_logout():
    """
    Handle user logout by clearing session state.
    """
    user_email = st.session_state.get('user', {}).get('email', 'Unknown')
    
    # Clear session state
    st.session_state.user = None
    st.session_state.user_id = None
    st.session_state.token = None
    st.session_state.current_chat_id = None
    st.session_state.chat_session = None
    
    print(f"👋 User logged out: {user_email}")


# ============================================================================
# LOGIN PAGE UI
# ============================================================================

def show_login_page():
    """
    Display the login page with Google Sign-In button.
    """
    st.markdown("""
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 50px;
        }
        .login-title {
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 1rem;
            text-align: center;
        }
        .login-subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 3rem;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">🤖 AI Chatbot</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Sign in to start chatting with AI</div>', unsafe_allow_html=True)
        
        # Initialize OAuth component
        oauth2 = get_oauth_component()
        
        # Show login button
        result = oauth2.authorize_button(
            name="Continue with Google",
            icon="https://www.google.com/favicon.ico",
            redirect_uri=config.REDIRECT_URI,
            scope="openid email profile",
            key="google_oauth",
            extras_params={"prompt": "consent", "access_type": "offline"}
        )
        
        # Handle the result
        if result and 'token' in result:
            handle_login(result['token'])
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Add some info
        st.info("🔒 Your data is secure. We only access your basic profile information.")


# ============================================================================
# USER PROFILE DISPLAY
# ============================================================================

def show_user_profile():
    """
    Display user profile in sidebar with logout option.
    """
    user = get_current_user()
    
    if user:
        st.sidebar.markdown("---")
        
        # User info
        col1, col2 = st.sidebar.columns([1, 3])
        
        with col1:
            if user.get('picture'):
                st.image(user['picture'], width=50)
            else:
                st.markdown("👤")
        
        with col2:
            st.markdown(f"**{user.get('name', 'User')}**")
            st.markdown(f"<small>{user.get('email', '')}</small>", unsafe_allow_html=True)
        
        # Logout button
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            handle_logout()
            st.rerun()