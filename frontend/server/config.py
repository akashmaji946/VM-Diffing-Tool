"""Configuration for Flask application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Server configuration for URL generation
    # Don't use SERVER_NAME to avoid 404 issues, use APPLICATION_ROOT instead
    PREFERRED_URL_SCHEME = os.environ.get('PREFERRED_URL_SCHEME', 'http')
    # Base URL for email links (set in .env)
    BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:8000')
    
    # Database
    BASE_DIR = Path(__file__).parent.parent.parent  # Project root
    DATABASE_DIR = BASE_DIR / "database"
    DATABASE_DIR.mkdir(exist_ok=True)  # Create database directory if it doesn't exist
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_DIR / "vmtool.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login
    REMEMBER_COOKIE_DURATION = 86400  # 1 day in seconds
    
    # Email configuration (for email verification)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@vmtool.local')
    
    # Email authentication method: 'oauth2' or 'password'
    MAIL_AUTH_METHOD = os.environ.get('MAIL_AUTH_METHOD', 'password')
    
    # Email verification
    EMAIL_VERIFICATION_REQUIRED = os.environ.get('EMAIL_VERIFICATION_REQUIRED', 'false').lower() in ['true', 'on', '1']
    EMAIL_VERIFICATION_TOKEN_MAX_AGE = 3600  # 1 hour