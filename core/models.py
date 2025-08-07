from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100))
    profile_id = db.Column(db.String(100), nullable=True)

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(100), db.ForeignKey('student.student_id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', backref=db.backref('attendances', lazy=True))