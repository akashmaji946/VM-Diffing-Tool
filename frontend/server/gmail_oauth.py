"""Gmail OAuth2 helper for sending emails."""
import os
import pickle
import base64
import logging
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

SCOPES = ["https://mail.google.com/"]
TOKEN_PATH = Path(__file__).parent / "token.pickle"
CREDENTIALS_PATH = Path(__file__).parent / "credentials.json"


def get_gmail_credentials():
    """Load or generate Gmail OAuth2 credentials."""
    creds = None
    
    if TOKEN_PATH.exists():
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                creds = None
        
        if not creds:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_PATH}. "
                    "Download it from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)

    return creds


def get_oauth2_string(user_email: str, creds: Credentials) -> str:
    """Generate OAuth2 authentication string for SMTP."""
    auth_string = f"user={user_email}\1auth=Bearer {creds.token}\1\1"
    return base64.b64encode(auth_string.encode()).decode()


def send_email_with_oauth2(mail, msg, sender_email: str):
    """Send email using Gmail OAuth2 authentication."""
    try:
        creds = get_gmail_credentials()
        
        with mail.connect() as conn:
            smtp = conn.host
            auth_string = get_oauth2_string(sender_email, creds)
            smtp.docmd("AUTH", "XOAUTH2 " + auth_string)
            smtp.send_message(msg)
        
        logger.info(f"Email sent successfully via OAuth2 to {msg.recipients}")
        return True
    except Exception as e:
        logger.exception(f"Failed to send email via OAuth2: {e}")
        return False
