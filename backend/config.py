import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration with secure defaults."""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///happy_place.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', '20')),
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '10')),
        'pool_timeout': 30
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv('JWT_ACCESS_EXPIRES_MINUTES', '15')))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv('JWT_REFRESH_EXPIRES_DAYS', '7')))
    JWT_IDENTITY_CLAIM = 'sub'
    JWT_ALGORITHM = 'HS256'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_ALLOW_HEADERS = ['Content-Type', 'Authorization']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    
    # Encryption Configuration
    ENCRYPTION_KEY_PRIMARY = os.getenv('ENCRYPTION_KEY_PRIMARY')
    ENCRYPTION_KEY_SECONDARY = os.getenv('ENCRYPTION_KEY_SECONDARY')

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', 'CHANGE_ME_GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET', 'CHANGE_ME_GOOGLE_CLIENT_SECRET')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200 per day, 50 per hour')

    @classmethod
    def validate_secrets(cls):
        """Validate critical secrets, especially in production."""
        flask_env = os.getenv('FLASK_ENV', 'development')
        errors = []

        if flask_env == 'production':
            # Validate JWT Secret
            if cls.JWT_SECRET_KEY == 'dev-secret-key-change-me':
                errors.append('JWT_SECRET_KEY must be set to a secure value in production')
            elif len(cls.JWT_SECRET_KEY) < 32:
                errors.append('JWT_SECRET_KEY must be at least 32 characters long')
            
            # Validate Flask Secret
            if cls.SECRET_KEY == 'dev-secret-key-change-me':
                errors.append('SECRET_KEY must be set to a secure value in production')
            elif len(cls.SECRET_KEY) < 32:
                errors.append('SECRET_KEY must be at least 32 characters long')
            
            # Validate Encryption Keys
            if not cls.ENCRYPTION_KEY_PRIMARY:
                errors.append('ENCRYPTION_KEY_PRIMARY is required in production')
            
            # Validate Database URL
            if 'sqlite' in cls.SQLALCHEMY_DATABASE_URI.lower():
                errors.append('SQLite is not suitable for production. Use PostgreSQL.')
            
            # Validate Google OAuth (if used)
            if cls.GOOGLE_CLIENT_ID == 'CHANGE_ME_GOOGLE_CLIENT_ID':
                errors.append('GOOGLE_CLIENT_ID must be configured if OAuth is enabled')
            
            if errors:
                raise RuntimeError(
                    'Production configuration validation failed:\n' + 
                    '\n'.join(f'  - {error}' for error in errors)
                )
