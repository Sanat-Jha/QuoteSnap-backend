#!/usr/bin/env python3
"""
Database initialization script for QuoteSnap.

This script creates the database tables and sets up the initial database structure.
Run this script before starting the application for the first time.
"""

import os
import sys
import logging

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.services.database_service import DatabaseService
from config.settings import Config

def initialize_database():
    """
    Initialize the QuoteSnap database with all required tables.
    """
    print("Initializing QuoteSnap database...")
    
    # Create database service instance
    db_service = DatabaseService(Config.DATABASE_URL.replace('sqlite:///', ''))
    
    # Connect to database
    if not db_service.connect():
        print("❌ Failed to connect to database")
        return False
    
    print("✅ Database connection established")
    
    # Create tables
    if not db_service.create_tables():
        print("❌ Failed to create database tables")
        return False
    
    print("✅ Database tables created successfully")
    
    # Log initialization
    db_service.log_event(
        level='INFO',
        category='system',
        message='Database initialized successfully',
        details={'tables_created': ['emails', 'quotation_requests', 'quotation_history', 'logs']}
    )
    
    print("✅ Database initialization completed")
    
    # Disconnect
    db_service.disconnect()
    
    return True

def check_database_status():
    """
    Check the current status of the database.
    """
    print("\nChecking database status...")
    
    db_service = DatabaseService(Config.DATABASE_URL.replace('sqlite:///', ''))
    
    if not db_service.connect():
        print("❌ Cannot connect to database")
        return
    
    # Get basic metrics
    metrics = db_service.get_metrics()
    
    print("📊 Database Status:")
    print(f"   - Total emails: {metrics.get('total_emails', 0)}")
    print(f"   - Total quotation requests: {metrics.get('total_quotation_requests', 0)}")
    print(f"   - Total quotations generated: {metrics.get('total_quotations_generated', 0)}")
    
    db_service.disconnect()

def reset_database():
    """
    Reset the database by dropping all tables and recreating them.
    """
    print("\n⚠️  RESETTING DATABASE - This will delete all data!")
    confirm = input("Are you sure you want to continue? (type 'yes' to confirm): ")
    
    if confirm.lower() != 'yes':
        print("Database reset cancelled")
        return
    
    db_path = Config.DATABASE_URL.replace('sqlite:///', '')
    
    # Delete database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print("✅ Existing database file deleted")
    
    # Recreate database
    initialize_database()

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    print("QuoteSnap Database Management")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "init":
            initialize_database()
        elif command == "status":
            check_database_status()
        elif command == "reset":
            reset_database()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, status, reset")
    else:
        print("Available commands:")
        print("  python init_db.py init    - Initialize database tables")
        print("  python init_db.py status  - Check database status")
        print("  python init_db.py reset   - Reset database (delete all data)")
        print()
        
        # Default action: initialize if database doesn't exist
        db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        if not os.path.exists(db_path):
            print("Database not found. Initializing...")
            initialize_database()
        else:
            print("Database already exists. Use 'status' to check or 'reset' to recreate.")
            check_database_status()