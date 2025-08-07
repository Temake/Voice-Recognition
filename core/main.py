from flask import Flask, render_template, request, jsonify
from .models import db, Student, Attendance
import requests
from .config import AZURE_REGION, API_KEY, SPEAKER_API
def create_or_get_student(student_id):
    student = Student.query.filter_by(student_id=student_id).first()
    if student:
        return student

    profile_id = create_profile_on_azure()
    student = Student(student_id=student_id, profile_id=profile_id)
    db.session.add(student)
    db.session.commit()
    return student

def create_profile_on_azure():
    url = f"{SPEAKER_API}/v2.0/verificationProfiles"
    response = requests.post(url, headers={
        "Ocp-Apim-Subscription-Key": API_KEY,
        "Content-Type": "application/json"
    }, json={"locale": "en-US"})

    return response.json().get("verificationProfileId")

def enroll_profile(profile_id, audio_path):
    url = f"{SPEAKER_API}/v2.0/verificationProfiles/{profile_id}/enroll"
    with open(audio_path, 'rb') as audio:
        response = requests.post(url, headers={
            "Ocp-Apim-Subscription-Key": API_KEY,
            "Content-Type": "audio/wav"
        }, data=audio)
    return response.status_code == 200

def verify_student(student, audio_path):
    url = f"{SPEAKER_API}/v2.0/verify?verificationProfileId={student.profile_id}"
    with open(audio_path, 'rb') as audio:
        response = requests.post(url, headers={
            "Ocp-Apim-Subscription-Key": API_KEY,
            "Content-Type": "audio/wav"
        }, data=audio)

    result = response.json()
    if result.get("result") == "Accept":
        mark_attendance(student.student_id)
        return True
    return False

def mark_attendance(student_id):
    record = Attendance(student_id=student_id)
    db.session.add(record)
    db.session.commit()
