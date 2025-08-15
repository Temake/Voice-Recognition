import os 
from datetime import datetime
import time 
from .constants import *
import json

class SecurityManager:
    def __init__(self):
        self.failed_attempts = {}
        self.rate_limits = {}
        # Keep file-based logging as backup while migrating
        self.security_log = self.load_security_log()
    
    def load_security_log(self):
        """Load security log from file (backup)"""
        try:
            with open(SECURITY_LOG_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_security_log(self):
        """Save security log to file (backup)"""
        try:
            with open(SECURITY_LOG_FILE, 'w') as f:
                json.dump(self.security_log, f, indent=2)
        except Exception as e:
            print(f"⚠️ Warning: Could not save security log to file: {e}")
    
    def log_security_event(self, event_type, student_id, details, ip_address=None, teacher_id=None):
        """Log security events to both database and file"""
        try:
            # Import here to avoid circular imports
            from .models import db, SecurityLog
            from flask_login import current_user
            
            # Use provided teacher_id or current user (with safety checks)
            if teacher_id is None and current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                teacher_id = current_user.id
            
            # Create database record if we have a teacher_id
            if teacher_id:
                event = SecurityLog(
                    teacher_id=teacher_id,
                    event_type=event_type,
                    student_id=student_id,
                    details=details,
                    ip_address=ip_address
                )
                db.session.add(event)
                db.session.commit()
            
            # Also keep file-based backup
            file_event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'student_id': student_id,
                'details': details,
                'ip_address': ip_address,
                'teacher_id': teacher_id
            }
            self.security_log.append(file_event)
            self.save_security_log()
            
            print(f"🔒 Security Event: {event_type} - {student_id} - {details}")
            
        except Exception as e:
            print(f"⚠️ Error logging security event: {e}")
            # Fall back to file logging only
            try:
                file_event = {
                    'timestamp': datetime.now().isoformat(),
                    'event_type': event_type,
                    'student_id': student_id,
                    'details': details,
                    'ip_address': ip_address,
                    'teacher_id': teacher_id
                }
                self.security_log.append(file_event)
                self.save_security_log()
            except Exception as e2:
                print(f"⚠️ Failed to save security log to file: {e2}")
    
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
        
        return len(self.failed_attempts[student_id]) >= 899
    
    def record_failed_attempt(self, student_id):
        """Record a failed verification attempt"""
        if student_id not in self.failed_attempts:
            self.failed_attempts[student_id] = []
        self.failed_attempts[student_id].append(time.time())

def allowed_file(filename):
    if not filename:
        return True
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

