from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime
import json

db = SQLAlchemy()
bcrypt = Bcrypt()

class Teacher(UserMixin, db.Model):
    """Teacher model for authentication"""
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(60), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    students = db.relationship('Student', backref='teacher', lazy=True, cascade='all, delete-orphan')
    attendance_records = db.relationship('AttendanceRecord', backref='teacher', lazy=True)
    security_logs = db.relationship('SecurityLog', backref='teacher', lazy=True)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return bcrypt.check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<Teacher {self.email}>'

class Student(db.Model):
    """Student model for enrollment"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False, index=True)
    student_name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    voice_features = db.Column(db.Text)  # JSON string of voice features
    voice_sample_url = db.Column(db.String(500))  # Cloudinary URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Composite unique constraint to prevent duplicate student IDs per teacher
    __table_args__ = (db.UniqueConstraint('student_id', 'teacher_id', name='unique_student_per_teacher'),)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True)
    
    def set_voice_features(self, features):
        """Store voice features as JSON"""
        self.voice_features = json.dumps(features.tolist() if hasattr(features, 'tolist') else features)
    
    def get_voice_features(self):
        """Retrieve voice features from JSON"""
        if self.voice_features:
            return json.loads(self.voice_features)
        return None
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.student_name}>'

class AttendanceRecord(db.Model):
    """Attendance record model"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    confidence_score = db.Column(db.Float)
    voice_sample_url = db.Column(db.String(500))  # Cloudinary URL for verification
    ip_address = db.Column(db.String(45))
    status = db.Column(db.String(20), default='present')  # present, late, etc.
    
    def __repr__(self):
        return f'<AttendanceRecord {self.student.student_id} at {self.timestamp}>'

class SecurityLog(db.Model):
    """Security log model"""
    __tablename__ = 'security_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    student_id = db.Column(db.String(50))  # Can be null for teacher-related events
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'student_id': self.student_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'teacher_id': self.teacher_id
        }
    
    def __repr__(self):
        return f'<SecurityLog {self.event_type} at {self.timestamp}>'
