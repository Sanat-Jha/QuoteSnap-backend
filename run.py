#!/usr/bin/env python3
"""
QuoteSnap application runner script.

This script starts the QuoteSnap Flask application with proper initialization.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

def main():
    """
    Main application entry point.
    """
    print("Starting QuoteSnap application...")
    
    # Import after setting up path
    import app as flask_app
    from config.settings import Config
    
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set")
        return 1
    
    # Get Flask app instance
    app = flask_app.app
    
    # Check if database exists and initialize if needed
    from app.services.database_service import DatabaseService
    
    db_service = DatabaseService()
    if db_service.connect():
        if not db_service.create_tables():
            print("⚠️  Warning: Could not create database tables")
        else:
            print("✅ Database ready")
        db_service.disconnect()
    else:
        print("⚠️  Warning: Could not connect to database")
    
    # Start the application
    print("🚀 QuoteSnap is starting on http://localhost:5000")
    print("📧 Gmail monitoring will start after authentication")
    print("📊 Dashboard available at http://localhost:5000")
    print("\nPress Ctrl+C to stop the application")
    
    try:
        app.run(
            debug=Config.DEBUG,
            host='0.0.0.0',
            port=5000,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n👋 QuoteSnap application stopped")
        return 0

if __name__ == "__main__":
    sys.exit(main())