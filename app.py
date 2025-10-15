"""
QuoteSnap - Gmail Email Monitor
Simple Gmail monitoring application that prints new emails.
"""

import logging
import os
import threading
from datetime import datetime
from flask import Flask, jsonify, send_file, redirect, session, request
from flask_cors import CORS
from dotenv import load_dotenv
from app.services.gmail_service import GmailService
from app.services.duckdb_service import DuckDBService
from app.services.new_excel_generation import ExcelGenerationService
from config.settings import Config

# Load environment variables
load_dotenv()

# Global Gmail service instance
gmail_service_instance = None
monitoring_active = False

def setup_logging():
    """Configure basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_flask_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    CORS(app, supports_credentials=True, origins=['http://localhost:5173', 'http://localhost:3000'])
    
    @app.route('/api/auth/status', methods=['GET'])
    def auth_status():
        """
        Check if user is authenticated with Gmail.
        
        Returns:
            JSON response with authentication status
        """
        try:
            token_path = Config.GMAIL_TOKEN_FILE
            
            if os.path.exists(token_path):
                # Token file exists, check if valid
                from google.oauth2.credentials import Credentials
                try:
                    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
                              'https://www.googleapis.com/auth/gmail.modify']
                    creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                    
                    if creds and creds.valid:
                        return jsonify({
                            'authenticated': True,
                            'message': 'User is authenticated'
                        })
                    elif creds and creds.expired and creds.refresh_token:
                        from google.auth.transport.requests import Request
                        try:
                            creds.refresh(Request())
                            # Save refreshed credentials
                            with open(token_path, 'w') as token:
                                token.write(creds.to_json())
                            return jsonify({
                                'authenticated': True,
                                'message': 'Token refreshed successfully'
                            })
                        except Exception as e:
                            logger.error(f"Failed to refresh token: {str(e)}")
                            return jsonify({
                                'authenticated': False,
                                'message': 'Token expired and refresh failed'
                            })
                except Exception as e:
                    logger.error(f"Error checking credentials: {str(e)}")
                    return jsonify({
                        'authenticated': False,
                        'message': 'Invalid credentials'
                    })
            
            return jsonify({
                'authenticated': False,
                'message': 'No authentication token found'
            })
            
        except Exception as e:
            logging.error(f"Auth status error: {str(e)}")
            return jsonify({'authenticated': False, 'error': str(e)}), 500
    
    @app.route('/api/auth/login', methods=['GET'])
    def auth_login():
        """
        Initiate Gmail OAuth flow.
        
        Returns:
            Redirect to Google OAuth or success message
        """
        global gmail_service_instance, monitoring_active
        
        try:
            gmail_service = GmailService(
                credentials_path=Config.GMAIL_CREDENTIALS_FILE,
                token_path=Config.GMAIL_TOKEN_FILE
            )
            
            if gmail_service.authenticate():
                # Store the service instance globally
                gmail_service_instance = gmail_service
                
                # Start monitoring if not already active
                if not monitoring_active:
                    import threading
                    monitoring_thread = threading.Thread(
                        target=start_monitoring_loop,
                        args=(gmail_service,),
                        daemon=True
                    )
                    monitoring_thread.start()
                    monitoring_active = True
                    logger.info("📧 Email monitoring started")
                
                return jsonify({
                    'success': True,
                    'message': 'Authentication successful',
                    'redirect': 'http://localhost:5173/dashboard'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Authentication failed'
                }), 401
                
        except Exception as e:
            logging.error(f"Auth login error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/auth/logout', methods=['POST'])
    def auth_logout():
        """
        Logout user by removing token file.
        
        Returns:
            JSON response confirming logout
        """
        global gmail_service_instance, monitoring_active
        
        try:
            token_path = Config.GMAIL_TOKEN_FILE
            if os.path.exists(token_path):
                os.remove(token_path)
            
            # Stop monitoring
            if gmail_service_instance:
                gmail_service_instance.stop_monitoring()
                gmail_service_instance = None
            monitoring_active = False
            
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            })
        except Exception as e:
            logging.error(f"Logout error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
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
    
    @app.route('/api/quotation/generate/<gmail_id>', methods=['GET'])
    def generate_quotation(gmail_id: str):
        """
        Generate and download Excel quotation file from stored email extraction data using the new ExcelGenerationService (win32com version).
        Args:
            gmail_id (str): Gmail message ID
        Returns:
            Excel file for immediate download
        """
        try:
            # Get email data from database
            db_service = DuckDBService()
            if not db_service.connect():
                return jsonify({'error': 'Failed to connect to database'}), 500
            extraction_data = db_service.get_extraction(gmail_id)
            db_service.disconnect()
            if not extraction_data:
                return jsonify({'error': f'Email with gmail_id {gmail_id} not found'}), 404
            # Check if it's a valid quotation (not irrelevant)
            if extraction_data.get('extraction_status') != 'VALID':
                return jsonify({
                    'error': 'Cannot generate quotation for irrelevant email',
                    'status': extraction_data.get('extraction_status')
                }), 400
            # Generate Excel file on disk using new service
            excel_service = ExcelGenerationService()
            output_file = excel_service.generate_quotation_excel(gmail_id, extraction_data)
            if not output_file or not os.path.exists(output_file):
                return jsonify({'error': 'Failed to generate Excel file'}), 500

            # Ensure the file is closed and saved before sending (important for win32com)
            # (Already handled in service, but double-check)
            import time
            time.sleep(0.2)  # Small delay to ensure file system flush (esp. on Windows)

            # Create a descriptive filename for download
            subject = extraction_data.get('subject', 'quotation')[:30]  # Limit length
            clean_subject = "".join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).rstrip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_filename = f"Quotation_{clean_subject}_{timestamp}.xlsx"

            # Open the file in binary mode and send as attachment (ensures no in-memory re-save)
            return send_file(
                os.path.abspath(output_file),
                as_attachment=True,
                download_name=download_filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                max_age=0  # Prevent caching
            )
        except Exception as e:
            logging.error(f"Quotation generation error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/quotation/download/<filename>', methods=['GET'])
    def download_quotation(filename: str):
        """
        Download generated quotation Excel file.
        
        Args:
            filename (str): Filename to download
            
        Returns:
            File download
        """
        try:
            file_path = os.path.join('generated', filename)
            
            if not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 404
            
            # Validate filename to prevent directory traversal
            if not filename.endswith('.xlsx') or '..' in filename:
                return jsonify({'error': 'Invalid filename'}), 400
            
            return send_file(
                file_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
        except Exception as e:
            logging.error(f"File download error: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    # The new ExcelGenerationService does not provide a template analysis method, so this endpoint is now deprecated or should be updated if needed.
    @app.route('/api/template/analyze', methods=['GET'])
    def analyze_template():
        """
        (Deprecated) Analyze the Excel template structure. Not supported in new ExcelGenerationService.
        """
        return jsonify({'success': False, 'error': 'Template analysis not supported in new ExcelGenerationService.'}), 501
    
    return app

def start_monitoring_loop(gmail_service):
    """
    Background thread function to monitor emails continuously.
    
    Args:
        gmail_service: Authenticated GmailService instance
    """
    try:
        logging.info(f"📧 Starting email monitoring (checking every {Config.EMAIL_CHECK_INTERVAL} seconds)")
        logging.info("📱 Monitoring active - new emails will be processed automatically")
        logging.info("=" * 60)
        
        gmail_service.start_monitoring(Config.EMAIL_CHECK_INTERVAL)
        
    except Exception as e:
        logging.error(f"Email monitoring error: {str(e)}")

def initialize_database():
    """Initialize DuckDB database on startup."""
    try:
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
    except Exception as e:
        print(f"❌ Database initialization error: {str(e)}")
        logging.error(f"Database initialization error: {str(e)}")

def check_and_start_monitoring_if_authenticated():
    """Check if user is already authenticated and start monitoring."""
    global gmail_service_instance, monitoring_active
    
    try:
        token_path = Config.GMAIL_TOKEN_FILE
        
        if os.path.exists(token_path):
            print("🔍 Found existing authentication token...")
            
            # Try to authenticate with existing token
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            
            SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
                      'https://www.googleapis.com/auth/gmail.modify']
            
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
                
                if creds and creds.valid:
                    # Valid token, start monitoring
                    print("✅ Token is valid, starting email monitoring...")
                    
                    gmail_service = GmailService(
                        credentials_path=Config.GMAIL_CREDENTIALS_FILE,
                        token_path=Config.GMAIL_TOKEN_FILE
                    )
                    gmail_service.credentials = creds
                    gmail_service.service = gmail_service._build_service()
                    
                    gmail_service_instance = gmail_service
                    
                    # Start monitoring in background
                    import threading
                    monitoring_thread = threading.Thread(
                        target=start_monitoring_loop,
                        args=(gmail_service,),
                        daemon=True
                    )
                    monitoring_thread.start()
                    monitoring_active = True
                    
                    print("📧 Email monitoring active")
                    return True
                    
                elif creds and creds.expired and creds.refresh_token:
                    # Try to refresh
                    print("🔄 Token expired, attempting to refresh...")
                    try:
                        creds.refresh(Request())
                        with open(token_path, 'w') as token:
                            token.write(creds.to_json())
                        print("✅ Token refreshed successfully")
                        
                        # Now start monitoring with refreshed token
                        gmail_service = GmailService(
                            credentials_path=Config.GMAIL_CREDENTIALS_FILE,
                            token_path=Config.GMAIL_TOKEN_FILE
                        )
                        gmail_service.credentials = creds
                        gmail_service.service = gmail_service._build_service()
                        
                        gmail_service_instance = gmail_service
                        
                        import threading
                        monitoring_thread = threading.Thread(
                            target=start_monitoring_loop,
                            args=(gmail_service,),
                            daemon=True
                        )
                        monitoring_thread.start()
                        monitoring_active = True
                        
                        print("📧 Email monitoring active")
                        return True
                        
                    except Exception as e:
                        print(f"⚠️ Failed to refresh token: {str(e)}")
                        print("💡 Please login via frontend to re-authenticate")
                        return False
                        
            except Exception as e:
                print(f"⚠️ Invalid token: {str(e)}")
                print("💡 Please login via frontend to re-authenticate")
                return False
        else:
            print("💡 No authentication token found. Please login via frontend.")
            return False
            
    except Exception as e:
        logging.error(f"Error checking authentication: {str(e)}")
        return False
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
        # Initialize database
        initialize_database()
        
        # Check if already authenticated and start monitoring
        check_and_start_monitoring_if_authenticated()
        
        # Create and run Flask API
        print("🌐 Starting Flask API server...")
        app = create_flask_app()
        print("📡 API Endpoints available:")
        print("   GET /api/auth/status - Check authentication status")
        print("   GET /api/auth/login - Login with Google")
        print("   POST /api/auth/logout - Logout")
        print("   GET /api/emails - Get all stored emails")
        print("   GET /api/emails/stats - Get email statistics")
        print("   GET /api/quotation/generate/<gmail_id> - Download quotation")
        print("   GET /api/health - Health check")
        print("🚀 Server running at http://localhost:5000")
        print("=" * 60)
        if not monitoring_active:
            print("💡 Tip: Email monitoring will start automatically when you login via frontend")
            print("=" * 60)
        
        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down SnapQuote...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logging.error(f"Application error: {str(e)}")

if __name__ == '__main__':
    main()