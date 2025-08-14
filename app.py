# app.py - Production Ready Version
from flask import Flask 
import os
from config.routes import config
from datetime import datetime

app = Flask(__name__)

# Production security configuration
app.secret_key = os.environ.get('SECRET_KEY', 'ah)vh+hug0)fo^-82@3sq(z77$9^+3q($=+k)zvuvhjm^w@5p*')

# Configure upload settings
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'voice_samples')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Production settings
app.config['ENV'] = os.environ.get('FLASK_ENV', 'production')
app.config['DEBUG'] = os.environ.get('FLASK_ENV', 'production') == 'development'

# Create required directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('uploads', exist_ok=True)
os.makedirs('data', exist_ok=True)  # For Docker volume mount

# Register blueprints
app.register_blueprint(config)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    app.run(debug=debug, port=port, host=host)

