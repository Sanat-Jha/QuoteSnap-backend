"""
QuoteSnap - Gmail Email Monitor
Simple Gmail monitoring application that prints new emails.
"""

import logging
import os
import threading
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from app.services.gmail_service import GmailService
from app.services.duckdb_service import DuckDBService
from config.settings import Config

# Load environment variables
load_dotenv()

def setup_logging():
    """Configure basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_flask_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    CORS(app)
    
    @app.route('/api/emails', methods=['GET'])
    def get_all_emails():
        """
        API endpoint to fetch all stored email extractions.
        
        Returns:
            JSON response with all email extraction records
        """
        try:
            db_service = DuckDBService()
            if not db_service.connect():
                return jsonify({'error': 'Failed to connect to database'}), 500
            
            # Debug: Check if table exists and has data
            try:
                count_result = db_service.connection.execute('SELECT COUNT(*) FROM email_extractions').fetchone()
                table_count = count_result[0] if count_result else 0
                logging.info(f"Database has {table_count} records")
            except Exception as e:
                logging.error(f"Error checking table: {str(e)}")
                return jsonify({'error': f'Database table error: {str(e)}'}), 500
            
            # Get all extractions (limit to 1000 for performance)
            extractions = db_service.get_all_extractions(limit=1000)
            db_service.disconnect()
            
            return jsonify({
                'success': True,
                'count': len(extractions),
                'table_count': table_count,
                'data': extractions
            })
            
        except Exception as e:
            logging.error(f"API error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/debug/database', methods=['GET'])
    def debug_database():
        """
        Debug endpoint to check database status and content.
        
        Returns:
            JSON response with database debug information
        """
        try:
            db_service = DuckDBService()
            if not db_service.connect():
                return jsonify({'error': 'Failed to connect to database'}), 500
            
            # Check if table exists
            tables = db_service.connection.execute("SHOW TABLES").fetchall()
            table_names = [table[0] for table in tables]
            
            # Check table schema if exists
            schema = None
            count = 0
            sample_data = []
            
            if 'email_extractions' in table_names:
                # Get table schema
                schema_result = db_service.connection.execute("DESCRIBE email_extractions").fetchall()
                schema = [{'column': row[0], 'type': row[1]} for row in schema_result]
                
                # Get count
                count_result = db_service.connection.execute('SELECT COUNT(*) FROM email_extractions').fetchone()
                count = count_result[0] if count_result else 0
                
                # Get sample data
                if count > 0:
                    sample_result = db_service.connection.execute('SELECT * FROM email_extractions LIMIT 3').fetchall()
                    sample_data = [list(row) for row in sample_result]
            
            db_service.disconnect()
            
            return jsonify({
                'success': True,
                'database_path': db_service.db_path,
                'tables': table_names,
                'email_extractions_exists': 'email_extractions' in table_names,
                'schema': schema,
                'record_count': count,
                'sample_data': sample_data
            })
            
        except Exception as e:
            logging.error(f"Database debug error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/emails/stats', methods=['GET'])
    def get_email_stats():
        """
        API endpoint to get email processing statistics.
        
        Returns:
            JSON response with statistics
        """
        try:
            db_service = DuckDBService()
            if not db_service.connect():
                return jsonify({'error': 'Failed to connect to database'}), 500
            
            # Get statistics
            total_result = db_service.connection.execute('SELECT COUNT(*) FROM email_extractions').fetchone()
            valid_result = db_service.connection.execute("SELECT COUNT(*) FROM email_extractions WHERE extraction_status = 'VALID'").fetchone()
            irrelevant_result = db_service.connection.execute("SELECT COUNT(*) FROM email_extractions WHERE extraction_status = 'IRRELEVANT'").fetchone()
            
            db_service.disconnect()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_emails': total_result[0] if total_result else 0,
                    'valid_quotations': valid_result[0] if valid_result else 0,
                    'irrelevant_emails': irrelevant_result[0] if irrelevant_result else 0
                }
            })
            
        except Exception as e:
            logging.error(f"API error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'success': True,
            'message': 'SnapQuote API is running',
            'timestamp': datetime.now().isoformat()
        })
    
    return app

def start_gmail_monitoring():
    """Start Gmail monitoring in a separate thread."""
    try:
        # Initialize DuckDB database
        print("🗄️ Initializing DuckDB database...")
        db_service = DuckDBService()
        if db_service.connect():
            if db_service.create_table():
                print("✅ DuckDB database ready")
            else:
                print("⚠️ Warning: Could not create database table")
            db_service.disconnect()
        else:
            print("⚠️ Warning: Could not connect to database")
        
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
        else:
            print("❌ Gmail authentication failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logging.error(f"Gmail monitoring error: {str(e)}")

def main():
    """Main application entry point."""
    print("🚀 Starting SnapQuote Gmail Monitor with API...")
    
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
        # Start Gmail monitoring in background thread
        monitoring_thread = threading.Thread(target=start_gmail_monitoring, daemon=True)
        monitoring_thread.start()
        
        # Create and run Flask API
        print("🌐 Starting Flask API server...")
        app = create_flask_app()
        print("📡 API Endpoints available:")
        print("   GET /api/emails - Get all stored emails")
        print("   GET /api/emails/stats - Get email statistics")
        print("   GET /api/health - Health check")
        print("🚀 Server running at http://localhost:5000")
        print("=" * 60)
        
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down SnapQuote...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logging.error(f"Application error: {str(e)}")

if __name__ == '__main__':
    main()