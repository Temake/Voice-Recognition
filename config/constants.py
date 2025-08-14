import os

# Security Configuration
SECURITY_LOG_FILE = os.environ.get('SECURITY_LOG_FILE', 'security_log.json')
SUSPICIOUS_ATTEMPT_THRESHOLD = int(os.environ.get('SUSPICIOUS_ATTEMPT_THRESHOLD', '9'))
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '300'))  # 5 minutes rate limiting

# File Storage Configuration
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'voice_samples')
ATTENDANCE_FILE = os.environ.get('ATTENDANCE_FILE', 'attendance_records.json')
VOICE_MODELS_FILE = os.environ.get('VOICE_MODELS_FILE', 'voice_models.pkl')

# Audio Configuration
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}
MIN_AUDIO_DURATION = float(os.environ.get('MIN_AUDIO_DURATION', '2.0'))
MAX_AUDIO_DURATION = float(os.environ.get('MAX_AUDIO_DURATION', '30.0'))
MIN_VOICE_THRESHOLD = float(os.environ.get('MIN_VOICE_THRESHOLD', '0.88'))

# Production Configuration
MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
DEBUG = os.environ.get('FLASK_ENV', 'production') == 'development' 
