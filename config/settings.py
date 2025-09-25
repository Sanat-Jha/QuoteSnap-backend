"""
Configuration settings for QuoteSnap application.

This module contains all configuration settings for different environments
(development, production, testing) and handles environment variable loading.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Base configuration class with common settings.
    """
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///database/quotesnap.db'
    
    # Gmail API Configuration
    GMAIL_CLIENT_ID = os.environ.get('GMAIL_CLIENT_ID')
    GMAIL_CLIENT_SECRET = os.environ.get('GMAIL_CLIENT_SECRET')
    GMAIL_REDIRECT_URI = os.environ.get('GMAIL_REDIRECT_URI') or 'http://localhost:5000/auth/callback'
    GMAIL_SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL') or 'gpt-3.5-turbo'
    
    # Email Monitoring Configuration
    EMAIL_CHECK_INTERVAL = int(os.environ.get('EMAIL_CHECK_INTERVAL', '300'))  # 5 minutes
    MAX_EMAILS_PER_CHECK = int(os.environ.get('MAX_EMAILS_PER_CHECK', '50'))
    
    # File Storage Configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'logs/app.log'
    
    # Excel Template Configuration
    EXCEL_TEMPLATE_PATH = os.environ.get('EXCEL_TEMPLATE_PATH') or 'templates/quotation_template.xlsx'
    
    @staticmethod
    def validate_config():
        """
        Validate that all required configuration values are present.
        
        Raises:
            ValueError: If required configuration is missing
        """
        required_vars = [
            'GMAIL_CLIENT_ID',
            'GMAIL_CLIENT_SECRET',
            'OPENAI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class DevelopmentConfig(Config):
    """
    Development environment configuration.
    """
    DEBUG = True
    DATABASE_URL = 'sqlite:///database/quotesnap_dev.db'

class ProductionConfig(Config):
    """
    Production environment configuration.
    """
    DEBUG = False
    # Use more secure settings in production
    
class TestingConfig(Config):
    """
    Testing environment configuration.
    """
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'  # In-memory database for testing

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}