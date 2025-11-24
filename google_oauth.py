"""
Google OAuth 2.0 Helper
Handles OAuth 2.0 flow for Google Sheets access in SaaS mode
"""

import os
import logging
from flask import session, redirect, request, url_for
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

# OAuth 2.0 scopes required for Google Sheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Default redirect URI (can be overridden)
DEFAULT_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/google/callback')


def get_oauth_flow(client_id: str, client_secret: str, redirect_uri: str = None):
    """
    Create OAuth 2.0 flow using user-provided credentials
    
    Args:
        client_id: User's Google OAuth Client ID
        client_secret: User's Google OAuth Client Secret
        redirect_uri: OAuth redirect URI
    
    Returns:
        Flow object
    """
    if not client_id or not client_secret:
        raise ValueError(
            "Google OAuth credentials are required. "
            "Please provide your Google OAuth Client ID and Client Secret."
        )
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri or DEFAULT_REDIRECT_URI]
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri or DEFAULT_REDIRECT_URI
    )
    
    return flow


def get_authorization_url(client_id: str, client_secret: str, redirect_uri: str = None):
    """
    Get Google OAuth authorization URL using user's credentials
    
    Args:
        client_id: User's Google OAuth Client ID
        client_secret: User's Google OAuth Client Secret
        redirect_uri: OAuth redirect URI
    
    Returns:
        Authorization URL string
    """
    flow = get_oauth_flow(client_id, client_secret, redirect_uri)
    
    # Store credentials and flow state in session for callback
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )
    
    session['oauth_state'] = state
    session['oauth_redirect_uri'] = redirect_uri or DEFAULT_REDIRECT_URI
    session['oauth_client_id'] = client_id
    session['oauth_client_secret'] = client_secret
    
    return authorization_url


def handle_oauth_callback(code: str, state: str):
    """
    Handle OAuth callback and exchange code for tokens using user's credentials
    
    Args:
        code: Authorization code from Google
        state: State parameter (should match session)
    
    Returns:
        Dictionary with token information
    """
    # Verify state
    if state != session.get('oauth_state'):
        raise ValueError("Invalid OAuth state parameter")
    
    # Get user's credentials from session
    client_id = session.get('oauth_client_id')
    client_secret = session.get('oauth_client_secret')
    
    if not client_id or not client_secret:
        raise ValueError("OAuth credentials not found in session. Please start the authorization process again.")
    
    redirect_uri = session.get('oauth_redirect_uri', DEFAULT_REDIRECT_URI)
    flow = get_oauth_flow(client_id, client_secret, redirect_uri)
    flow.fetch_token(code=code)
    
    # Get credentials
    creds = flow.credentials
    
    # Store token info in session (with user's client credentials)
    token_info = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': client_id,
        'client_secret': client_secret,
        'scopes': creds.scopes or SCOPES
    }
    
    session['google_oauth_token'] = token_info
    
    # Clear OAuth state (but keep credentials for future use)
    session.pop('oauth_state', None)
    session.pop('oauth_redirect_uri', None)
    
    logger.info("OAuth token stored in session")
    return token_info


def get_stored_credentials():
    """
    Get stored OAuth credentials from session
    
    Returns:
        Credentials object or None
    """
    token_info = session.get('google_oauth_token')
    if not token_info:
        return None
    
    creds = Credentials(
        token=token_info.get('token'),
        refresh_token=token_info.get('refresh_token'),
        token_uri=token_info.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=token_info.get('client_id'),
        client_secret=token_info.get('client_secret'),
        scopes=token_info.get('scopes', SCOPES)
    )
    
    # Refresh if expired
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Update session with new token
            token_info['token'] = creds.token
            session['google_oauth_token'] = token_info
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    return creds


def is_configured():
    """Check if user has provided OAuth credentials in session"""
    # Check if user has provided their own credentials
    return bool(session.get('google_oauth_client_id') or session.get('google_oauth_token'))


def is_authorized():
    """Check if user has authorized Google Sheets access"""
    return 'google_oauth_token' in session


def revoke_authorization():
    """Revoke Google Sheets authorization"""
    session.pop('google_oauth_token', None)
    logger.info("Google OAuth authorization revoked")

