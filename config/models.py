# config/models.py
from datetime import datetime
from config.database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    voice_sample_path = db.Column(db.String(255), nullable=True)
    voice_features = db.Column(db.Text, nullable=True)  # JSON string of voice features
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship with attendance records
    attendance_records = db.relationship('AttendanceRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    confidence_score = db.Column(db.Float, nullable=True)  # Voice recognition confidence
    audio_file_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='present')  # present, absent, late
    verified = db.Column(db.Boolean, default=True)  # Manual verification if needed
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<AttendanceRecord User:{self.user_id} at {self.timestamp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.name if self.user else None,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'confidence_score': self.confidence_score,
            'status': self.status,
            'verified': self.verified,
            'notes': self.notes
        }

class SystemLog(db.Model):
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(10), nullable=False)  # INFO, WARNING, ERROR
    message = db.Column(db.Text, nullable=False)
    module = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    
    def __repr__(self):
        return f'<SystemLog {self.level}: {self.message[:50]}...>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'message': self.message,
            'module': self.module,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'ip_address': self.ip_address
        }
