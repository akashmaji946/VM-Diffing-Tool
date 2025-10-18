"""Database models for user authentication."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self, secret_key: str) -> str:
        """Generate a verification token for email confirmation."""
        serializer = URLSafeTimedSerializer(secret_key)
        return serializer.dumps(self.email, salt='email-verification')
    
    @staticmethod
    def verify_token(token: str, secret_key: str, max_age: int = 3600) -> str | None:
        """Verify a token and return the email if valid."""
        serializer = URLSafeTimedSerializer(secret_key)
        try:
            email = serializer.loads(token, salt='email-verification', max_age=max_age)
            return email
        except Exception:
            return None
    
    def __repr__(self) -> str:
        return f'<User {self.username}>'
