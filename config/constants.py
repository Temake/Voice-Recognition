import os

DATABASE_URL = os.environ.get('DATABASE_URL')

CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
SECURITY_LOG_FILE = os.environ.get('SECURITY_LOG_FILE', 'security_log.json')
SUSPICIOUS_ATTEMPT_THRESHOLD = int(os.environ.get('SUSPICIOUS_ATTEMPT_THRESHOLD', '3'))
RATE_LIMIT_WINDOW = int(os.environ.get('RATE_LIMIT_WINDOW', '300')) 
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'voice_samples')
ATTENDANCE_FILE = os.environ.get('ATTENDANCE_FILE', 'attendance_records.json')
VOICE_MODELS_FILE = os.environ.get('VOICE_MODELS_FILE', 'voice_models.pkl')

ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}
MIN_AUDIO_DURATION = float(os.environ.get('MIN_AUDIO_DURATION', '2.0'))
MAX_AUDIO_DURATION = float(os.environ.get('MAX_AUDIO_DURATION', '30.0'))
MIN_VOICE_THRESHOLD = float(os.environ.get('MIN_VOICE_THRESHOLD', '0.7'))

MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '16777216'))  
DEBUG = os.environ.get('FLASK_ENV', 'production') == 'development' 
