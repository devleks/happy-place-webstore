import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///happy_place.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_IDENTITY_CLAIM = 'sub'  # Use 'sub' claim for identity
    JWT_ALGORITHM = 'HS256'

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'CHANGE_ME_GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'CHANGE_ME_GOOGLE_CLIENT_SECRET')

    @classmethod
    def validate_secrets(cls):
        """Validate critical secrets, especially in production."""
        flask_env = os.getenv('FLASK_ENV', 'development')

        if flask_env == 'production' and cls.JWT_SECRET_KEY == 'dev-secret-key-change-me':
            raise RuntimeError('JWT_SECRET_KEY must be set to a secure value in production')
