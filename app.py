"""
QuoteSnap - Gmail Email Monitor
Simple Gmail monitoring application that prints new emails.
"""

import logging
import os
from dotenv import load_dotenv
from app.services.gmail_service import GmailService
from config.settings import Config

# Load environment variables
load_dotenv()

def setup_logging():
    """Configure basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def main():
    """Main application entry point."""
    print("🚀 Starting Gmail Email Monitor...")
    
    # Configure logging
    setup_logging()
    
    # Validate configuration
    try:
        Config.validate_config()
        print("✅ Configuration validated")
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return
    
    try:
        # Initialize Gmail service
        gmail_service = GmailService(
            credentials_path=Config.GMAIL_CREDENTIALS_FILE,
            token_path=Config.GMAIL_TOKEN_FILE
        )
        
        # Authenticate with Gmail
        print("🔐 Authenticating with Gmail...")
        if gmail_service.authenticate():
            print("✅ Gmail authentication successful")
            
            # Start monitoring emails
            print(f"📧 Starting email monitoring (checking every {Config.EMAIL_CHECK_INTERVAL} seconds)")
            print("📱 Monitoring active - new emails will be displayed below:")
            print("=" * 60)
            
            gmail_service.start_monitoring(Config.EMAIL_CHECK_INTERVAL)
            
            # Keep the main thread alive
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Stopping email monitor...")
                gmail_service.stop_monitoring()
                
        else:
            print("❌ Failed to authenticate with Gmail")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == '__main__':
    main()

from flask import Flask, render_template, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import threading
import logging
from datetime import datetime

# Import custom modules
from app.routes.auth_routes import auth_bp
from app.routes.email_routes import email_bp
from app.routes.quotation_routes import quotation_bp
from app.routes.dashboard_routes import dashboard_bp
from app.services.gmail_service import GmailService
from app.services.database_service import DatabaseService
from config.settings import Config

# Load environment variables
load_dotenv()

def create_app():
    """
    Factory function to create and configure the Flask application.
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS for frontend communication
    CORS(app)
    
    # Configure logging
    setup_logging()
    
    # Initialize database
    init_database()
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize background services
    init_background_services()
    
    return app

def setup_logging():
    """
    Configure logging for the application.
    Sets up file and console logging with appropriate levels.
    """
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

def init_database():
    """
    Initialize the SQLite database and create tables if they don't exist.
    """
    db_service = DatabaseService()
    if db_service.connect():
        success = db_service.create_tables()
        db_service.disconnect()
        if success:
            logging.info("Database initialized successfully")
        else:
            logging.error("Failed to initialize database")
    else:
        logging.error("Failed to connect to database")

def register_blueprints(app):
    """
    Register all Flask blueprints for different route modules.
    
    Args:
        app (Flask): Flask application instance
    """
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(email_bp, url_prefix='/api/emails')
    app.register_blueprint(quotation_bp, url_prefix='/api/quotations')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

def init_background_services():
    """
    Initialize and start background services like Gmail monitoring.
    """
    try:
        # Initialize Gmail service
        gmail_service = GmailService(
            credentials_path=Config.GMAIL_CREDENTIALS_FILE,
            token_path=Config.GMAIL_TOKEN_FILE
        )
        
        # Authenticate with Gmail
        if gmail_service.authenticate():
            # Start monitoring emails
            check_interval = int(os.getenv('EMAIL_CHECK_INTERVAL', 60))
            gmail_service.start_monitoring(check_interval)
            logging.info("Gmail monitoring service started")
        else:
            logging.error("Failed to authenticate with Gmail")
            
    except Exception as e:
        logging.error(f"Failed to initialize background services: {str(e)}")

# Main Flask routes
app = create_app()

@app.route('/')
def index():
    """
    Main landing page route.
    
    Returns:
        str: Rendered HTML template for the main dashboard
    """
    return render_template('dashboard.html')

@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring system status.
    
    Returns:
        dict: JSON response with system health information
    """
    # Check database connectivity
    db_status = 'disconnected'
    try:
        db_service = DatabaseService()
        if db_service.connect():
            db_status = 'connected'
            db_service.disconnect()
    except:
        pass
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'database': db_status,
            'gmail_api': 'connected',
            'background_services': 'running'
        }
    })

@app.route('/api/status')
def get_status():
    """
    API endpoint to get current system status and metrics.
    
    Returns:
        dict: JSON response with system status and metrics
    """
    # TODO: Implement status endpoint
    # - Return email processing statistics
    # - Show quota usage
    # - Display recent activity summary
    return jsonify({
        'emails_processed': 0,
        'quotations_generated': 0,
        'last_check': None,
        'system_uptime': '0 hours'
    })

if __name__ == '__main__':
    """
    Run the Flask application in development mode.
    """
    # TODO: Add development-specific configurations
    # - Enable debug mode
    # - Set up hot reloading
    # - Configure development database
    app.run(debug=True, host='0.0.0.0', port=5000)