import os 
from datetime import datetime
import time 
from .constants import *
import json





class SecurityManager:
    def __init__(self):
        self.failed_attempts = {}
        self.rate_limits = {}
        self.security_log = self.load_security_log()
    
    def load_security_log(self):
        """Load security log from file"""
        try:
            with open(SECURITY_LOG_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_security_log(self):
        """Save security log to file"""
        with open(SECURITY_LOG_FILE, 'w') as f:
            json.dump(self.security_log, f, indent=2)
    
    def log_security_event(self, event_type, student_id, details, ip_address=None):
        """Log security events"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'student_id': student_id,
            'details': details,
            'ip_address': ip_address
        }
        self.security_log.append(event)
        self.save_security_log()
        print(f"🔒 Security Event: {event_type} - {student_id} - {details}")
    
    def check_rate_limit(self, identifier):
        """Check if identifier is rate limited"""
        current_time = time.time()
        if identifier in self.rate_limits:
            if current_time - self.rate_limits[identifier] < RATE_LIMIT_WINDOW:
                return False
        return True
    
    def apply_rate_limit(self, identifier):
        """Apply rate limit to identifier"""
        self.rate_limits[identifier] = time.time()
    
    def check_suspicious_activity(self, student_id):
        """Check for suspicious activity patterns"""
        current_time = time.time()
        if student_id not in self.failed_attempts:
            self.failed_attempts[student_id] = []
        
        # Clean old attempts (older than 1 hour)
        self.failed_attempts[student_id] = [
            attempt for attempt in self.failed_attempts[student_id] 
            if current_time - attempt < 3600
        ]
        
        return len(self.failed_attempts[student_id]) >= SUSPICIOUS_ATTEMPT_THRESHOLD
    
    def record_failed_attempt(self, student_id):
        """Record a failed verification attempt"""
        if student_id not in self.failed_attempts:
            self.failed_attempts[student_id] = []
        self.failed_attempts[student_id].append(time.time())

def allowed_file(filename):
    if not filename:
        return True
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

