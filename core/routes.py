from .config import *
from .models import db, Student, Attendance
from flask import  render_template, request, jsonify
import os
from .main import *
from ..main import app

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/handle_audio', methods=['POST'])
def handle_audio():
    audio = request.files['audio']
    student_id = request.form['student_id']
    action = request.form['action']

    filename = f"{student_id}.wav"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    audio.save(filepath)

    student = create_or_get_student(student_id)

    if action == 'enroll':
        success = enroll_profile(student.profile_id, filepath)
        message = "Enrollment Successful!" if success else "Enrollment Failed."
    elif action == 'verify':
        success = verify_student(student, filepath)
        message = "Attendance Marked ✅" if success else "Verification Failed ❌"
    else:
        message = "Invalid action."

    return jsonify(message=message)

@app.route('/attendance')
def view_attendance():
    records = Attendance.query.order_by(Attendance.timestamp.desc()).all()
    return render_template('attendance.html', records=records)
