import os

# Security Configuration
SECURITY_LOG_FILE = os.environ.get('SECURITY_LOG_FILE')
SUSPICIOUS_ATTEMPT_THRESHOLD = int(os.environ.get('SUSPICIOUS_ATTEMPT_THRESHOLD'))
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '300'))  # 5 minutes rate limiting

# File Storage Configuration
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')
ATTENDANCE_FILE = os.environ.get('ATTENDANCE_FILE')
VOICE_MODELS_FILE = os.environ.get('VOICE_MODELS_FILE')

# Audio Configuration
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}
MIN_AUDIO_DURATION = float(os.environ.get('MIN_AUDIO_DURATION', '2.0'))
MAX_AUDIO_DURATION = float(os.environ.get('MAX_AUDIO_DURATION'))
MIN_VOICE_THRESHOLD = float(os.environ.get('MIN_VOICE_THRESHOLD'))

# Production Configuration
MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
DEBUG = os.environ.get('FLASK_ENV', 'production') == 'development' 
