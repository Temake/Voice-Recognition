from flask import Flask, render_template, request, jsonify, Blueprint, current_app
from .voicerecognition import voice_system,MAX_AUDIO_DURATION,MIN_AUDIO_DURATION,MIN_VOICE_THRESHOLD,ALLOWED_EXTENSIONS
import json
from .security import allowed_file
from werkzeug.utils import secure_filename
import os
from datetime import datetime

config = Blueprint('config', __name__, template_folder='../templates')

@config.route('/welcome')
def welcome():
    """Landing page for new users"""
    return render_template('welcome.html')

@config.route('/dashboard')
def index():
    """Main dashboard with security overview"""
    students = voice_system.get_all_students()
    today_attendance = voice_system.get_attendance_report()
    security_events = voice_system.get_security_report(1)  # Last 24 hours
    return render_template('index.html', 
                         students=students, 
                         attendance=today_attendance,
                         security_events_count=len(security_events))

@config.route('/enroll')
def enroll_page():
    """Student enrollment page"""
    return render_template('enroll.html')

@config.route('/enroll_student', methods=['POST'])
def enroll_student():
    """Handle enhanced student enrollment"""
    try:
        student_id = request.form.get('student_id')
        student_name = request.form.get('student_name')
        client_ip = request.environ.get('REMOTE_ADDR', 'unknown')
        
        print(f"🎓 Enrollment request from {client_ip} for: {student_id}, Name: {student_name}")
        
        if not student_id or not student_name:
            return jsonify({'success': False, 'message': 'Student ID and name are required'}), 400
        
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
            # Generate secure filename
            file_ext = 'wav'
            if audio_file.filename and '.' in audio_file.filename:
                file_ext = audio_file.filename.rsplit('.', 1)[1].lower()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"{student_id}_enrollment_{timestamp}.{file_ext}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(filepath)
            
            success, message = voice_system.enroll_student(student_id, student_name, filepath)
            
            # Clean up temporary file
            try:
                os.remove(filepath)
            except OSError:
                pass
            
            # Log the enrollment attempt
            voice_system.security_manager.log_security_event(
                "ENROLLMENT_REQUEST", 
                student_id, 
                f"Enrollment {'successful' if success else 'failed'}: {message}",
                client_ip
            )
            
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
def attendance_page():
    """Attendance marking page"""
    students = voice_system.get_all_students()
    return render_template('attendance.html', students=students)

@config.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    """Handle enhanced attendance marking"""
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
            # Generate secure filename
            file_ext = 'wav'
            if audio_file.filename and '.' in audio_file.filename:
                file_ext = audio_file.filename.rsplit('.', 1)[1].lower()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = secure_filename(f"{student_id}_attendance_{timestamp}.{file_ext}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(filepath)
            
            success, message = voice_system.mark_attendance(student_id, filepath)
            
            # Clean up temporary file
            try:
                os.remove(filepath)
            except OSError:
                pass
            
            # Log the attendance attempt
            voice_system.security_manager.log_security_event(
                "ATTENDANCE_REQUEST", 
                student_id, 
                f"Attendance {'successful' if success else 'failed'}: {message}",
                client_ip
            )
            
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
def reports_page():
    """Enhanced reports page with security information"""
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
def security_page():
    """Security dashboard"""
    security_events = voice_system.get_security_report(30)  # Last 30 days
    return render_template('security.html', security_events=security_events)

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