# app.py - Production Ready Version with Authentication
from flask import Flask, redirect, url_for, request
from flask_login import LoginManager, login_required, current_user
import os
from datetime import datetime
from config.constants import *
from config.models import db, Teacher, bcrypt
from config.routes import config
from config.auth_routes import auth

def create_app():
    app = Flask(__name__)
    
    # Production security configuration
    app.secret_key = os.environ.get('SECRET_KEY', 'ah)vh+hug0)fo^-82@3sq(z77$9^+3q($=+k)zvuvhjm^w@5p*')
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///voice_attendance.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configure upload settings
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'voice_samples')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
    
    # Production settings
    app.config['ENV'] = os.environ.get('FLASK_ENV', 'production')
    app.config['DEBUG'] = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return Teacher.query.get(int(user_id))
    
    # Create required directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('data', exist_ok=True)  # For Docker volume mount
    
    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(config)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Main route redirect based on authentication
    @app.route('/')
    def home():
        """Redirect based on authentication status"""
        if current_user.is_authenticated:
            return redirect(url_for('config.index'))
        else:
            return redirect(url_for('config.welcome'))
    
    # Public enrollment route for students (no auth required)
    @app.route('/enroll')
    def public_enroll():
        """Public enrollment page for students"""
        teacher_id = request.args.get('teacher')
        if teacher_id:
            teacher = Teacher.query.get(teacher_id)
            if teacher:
                return redirect(url_for('config.enroll_page', teacher_id=teacher_id))
        return redirect(url_for('config.welcome'))
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    app.run(debug=debug, port=port, host=host)

