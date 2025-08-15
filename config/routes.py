from flask import Flask, render_template, request, jsonify, Blueprint, current_app
from flask_login import login_required, current_user
from .voicerecognition import voice_system,MAX_AUDIO_DURATION,MIN_AUDIO_DURATION,MIN_VOICE_THRESHOLD,ALLOWED_EXTENSIONS
from .models import db, Student, Teacher
import json
from .security import allowed_file
from .cloudinary_service import cloudinary_service
from werkzeug.utils import secure_filename
import os
from datetime import datetime

config = Blueprint('config', __name__, template_folder='../templates')

@config.route('/welcome')
def welcome():
    """Landing page for new users and students"""
    return render_template('welcome.html')

@config.route('/dashboard')
@login_required
def index():
    """Main dashboard with security overview - Teachers only"""
    students = voice_system.get_all_students()
    today_attendance = voice_system.get_attendance_report()
    security_events = voice_system.get_security_report(1)  # Last 24 hours
    return render_template('index.html', 
                         students=students, 
                         attendance=today_attendance,
                         security_events_count=len(security_events),
                         teacher=current_user)

@config.route('/enroll')
def enroll_page():
    """Student enrollment page - Public but with teacher reference"""
    teacher_id = request.args.get('teacher_id')
    teacher = None
    if teacher_id:
        teacher = Teacher.query.get(teacher_id)
    return render_template('enroll.html', teacher=teacher)

@config.route('/enroll_student', methods=['POST'])
def enroll_student():
    """Handle student enrollment - Public endpoint with teacher reference"""
    try:
        student_id = request.form.get('student_id')
        student_name = request.form.get('student_name')
        teacher_id = request.form.get('teacher_id')
        client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
        
        print(f"🎓 Enrollment request from {client_ip} for: {student_id}, Name: {student_name}, Teacher: {teacher_id}")
        
        if not all([student_id, student_name, teacher_id]):
            return jsonify({'success': False, 'message': 'Student ID, name, and teacher are required'}), 400
        
        # Validate teacher exists
        teacher = Teacher.query.get(teacher_id)
        if not teacher or not teacher.is_active:
            return jsonify({'success': False, 'message': 'Invalid teacher reference'}), 400
        
        # Validate input format
        if len(student_id) < 3 or len(student_name) < 2:
            return jsonify({'success': False, 'message': 'Student ID and name must be valid'}), 400
        
        # Check for audio file
        audio_file = None
        if 'recorded_audio' in request.files and request.files['recorded_audio'].filename:
            audio_file = request.files['recorded_audio']
        elif 'voice_sample' in request.files and request.files['voice_sample'].filename:
            audio_file = request.files['voice_sample']
        
        if not audio_file:
            return jsonify({'success': False, 'message': 'Voice sample is required for enrollment'}), 400
        
        if audio_file and allowed_file(audio_file.filename):
            # Save temporary file
            temp_file_path = cloudinary_service.save_temp_file(audio_file)
            if not temp_file_path:
                return jsonify({'success': False, 'message': 'Failed to process audio file'}), 400
            
            try:
                # Temporarily set current user context for enrollment
                from flask_login import login_user, logout_user
                was_authenticated = current_user.is_authenticated
                current_teacher = current_user if was_authenticated else None
                
                if not was_authenticated:
                    login_user(teacher, remember=False)
                
                success, message = voice_system.enroll_student(student_id, student_name, temp_file_path)
                
                # Restore authentication state
                if not was_authenticated:
                    logout_user()
                    if current_teacher:
                        login_user(current_teacher, remember=False)
                
            finally:
                # Clean up temporary file
                cloudinary_service.cleanup_temp_file(temp_file_path)
            
            return jsonify({
                'success': success,
                'message': message
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Invalid file format. Please upload WAV, MP3, or M4A files.'
            }), 400
    
    except Exception as e:
        print(f"❌ Error in enroll_student: {e}")
        return jsonify({
            'success': False,
            'message': f'An error occurred during enrollment'
        }), 500

@config.route('/attendance')
@login_required
def attendance_page():
    """Attendance marking page - Teachers only"""
    students = voice_system.get_all_students()
    return render_template('attendance.html', students=students)

@config.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    """Handle attendance marking - Teachers only"""
    try:
        student_id = request.form.get('student_id')
        client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
        
        print(f"📝 Attendance request from {client_ip} for Student ID: {student_id}")
       
        if not student_id:
            return jsonify({'success': False, 'message': 'Please select a student'}), 400
        
        # Check for audio file
        audio_file = None
        if 'recorded_audio' in request.files and request.files['recorded_audio'].filename:
            audio_file = request.files['recorded_audio']
        elif 'voice_sample' in request.files and request.files['voice_sample'].filename:
            audio_file = request.files['voice_sample']
        
        if not audio_file:
            return jsonify({'success': False, 'message': 'Voice sample is required for attendance'}), 400
        
        if audio_file and allowed_file(audio_file.filename):
            # Save temporary file
            temp_file_path = cloudinary_service.save_temp_file(audio_file)
            if not temp_file_path:
                return jsonify({'success': False, 'message': 'Failed to process audio file'}), 400
            
            try:
                success, message = voice_system.mark_attendance(student_id, temp_file_path)
                
                # Set IP address in the last attendance record if successful
                if success:
                    from .models import AttendanceRecord
                    recent_record = AttendanceRecord.query.filter_by(
                        teacher_id=current_user.id
                    ).order_by(AttendanceRecord.timestamp.desc()).first()
                    
                    if recent_record:
                        recent_record.ip_address = client_ip
                        db.session.commit()
                        
            finally:
                # Clean up temporary file
                cloudinary_service.cleanup_temp_file(temp_file_path)
            
            return jsonify({'success': success, 'message': message})
        else:
            return jsonify({
                'success': False, 
                'message': 'Invalid file format. Please upload WAV, MP3, or M4A files.'
            }), 400
    
    except Exception as e:
        print(f"❌ Error in mark_attendance: {e}")
        return jsonify({
            'success': False,
            'message': f'An error occurred while marking attendance'
        }), 500

@config.route('/reports')
@login_required
def reports_page():
    """Enhanced reports page with security information - Teachers only"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance = voice_system.get_attendance_report(date)
    all_students = voice_system.get_all_students()
    security_events = voice_system.get_security_report(7)  # Last 7 days
    return render_template('reports.html', 
                         attendance=attendance, 
                         date=date, 
                         all_students=all_students,
                         security_events=security_events)

@config.route('/security')
@login_required
def security_page():
    """Security dashboard - Teachers only"""
    security_events = voice_system.get_security_report(30)  # Last 30 days
    return render_template('security.html', security_events=security_events)

# Teacher sharing route
@config.route('/share_link')
@login_required
def share_link():
    """Generate enrollment link for teachers to share with students"""
    base_url = request.url_root.rstrip('/')
    enrollment_link = f"{base_url}/enroll?teacher_id={current_user.id}"
    return jsonify({
        'success': True,
        'enrollment_link': enrollment_link,
        'teacher_name': current_user.full_name
    })

@config.route('/api/system_status')
def system_status():
    """Enhanced API endpoint with security status"""
    try:
        students = voice_system.get_all_students()
        attendance_today = voice_system.get_attendance_report()
        security_events_today = voice_system.get_security_report(1)
        
        # Security statistics
        failed_attempts = sum(1 for event in security_events_today 
                            if event['event_type'] in ['FAILED_VOICE_VERIFICATION', 'SUSPICIOUS_ACTIVITY_DETECTED'])
        
        status = {
            'system_ready': True,
            'enrolled_students': len(students),
            'attendance_today': len(attendance_today),
            'security': {
                'events_today': len(security_events_today),
                'failed_attempts_today': failed_attempts,
                'voice_threshold': MIN_VOICE_THRESHOLD,
                'min_audio_duration': MIN_AUDIO_DURATION,
                'max_audio_duration': MAX_AUDIO_DURATION
            },
            'configuration': {
                'allowed_extensions': list(ALLOWED_EXTENSIONS),
                'max_file_size_mb': current_app.config.get('MAX_CONTENT_LENGTH', 16*1024*1024) / (1024 * 1024),
                'feature_version': '2.0'
            }
        }
        
        return jsonify(status)
    
    except Exception as e:
        return jsonify({
            'system_ready': False,
            'error': 'Failed to retrieve system status',
            'message': str(e)
        }), 500