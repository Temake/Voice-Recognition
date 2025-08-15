#!/usr/bin/env python3
"""
Voice Attendance System - Database Migration Script
This script helps migrate from file-based storage to PostgreSQL + Cloudinary
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from config.models import db

def create_database_tables():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Print table info
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"📊 Created tables: {', '.join(tables)}")

def check_environment():
    """Check if all required environment variables are set"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'CLOUDINARY_CLOUD_NAME',
        'CLOUDINARY_API_KEY',
        'CLOUDINARY_API_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables before running the migration.")
        print("See env.example for reference.")
        return False
    
    print("✅ All required environment variables are set!")
    return True

if __name__ == "__main__":
    print("🚀 Voice Attendance System - Database Migration")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    try:
        # Create database tables
        create_database_tables()
        
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Register a teacher account at /auth/register")
        print("2. Login and get your enrollment link")
        print("3. Share the enrollment link with students")
        print("4. Students can enroll using the shared link")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
