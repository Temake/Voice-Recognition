# config/database.py
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Flask app"""
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Fallback to individual components
        db_host = os.environ.get('DB_HOST', 'localhost')
        db_port = os.environ.get('DB_PORT', '5432')
        db_name = os.environ.get('DB_NAME', 'voiceattendance')
        db_user = os.environ.get('DB_USER', 'postgres')
        db_password = os.environ.get('DB_PASSWORD', 'password')
        
        database_url = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    return db
