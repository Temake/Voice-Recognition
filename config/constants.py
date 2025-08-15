import os

# Database Configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

# Cloudinary Configuration
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# Security Configuration
SECURITY_LOG_FILE = os.environ.get('SECURITY_LOG_FILE', 'security_log.json')
SUSPICIOUS_ATTEMPT_THRESHOLD = int(os.environ.get('SUSPICIOUS_ATTEMPT_THRESHOLD', '3'))
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '300'))  # 5 minutes rate limiting

# File Storage Configuration (Legacy support)
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'voice_samples')
ATTENDANCE_FILE = os.environ.get('ATTENDANCE_FILE', 'attendance_records.json')
VOICE_MODELS_FILE = os.environ.get('VOICE_MODELS_FILE', 'voice_models.pkl')

# Audio Configuration
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}
MIN_AUDIO_DURATION = float(os.environ.get('MIN_AUDIO_DURATION', '2.0'))
MAX_AUDIO_DURATION = float(os.environ.get('MAX_AUDIO_DURATION', '30.0'))
MIN_VOICE_THRESHOLD = float(os.environ.get('MIN_VOICE_THRESHOLD', '0.7'))

# Production Configuration
MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
DEBUG = os.environ.get('FLASK_ENV', 'production') == 'development' 
