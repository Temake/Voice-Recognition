# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import pickle
import numpy as np
from datetime import datetime
import librosa
import soundfile as sf
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ah)vh+hug0)fo^-82@3sq(z77$9^+3q($=+k)zvuvhjm^w@5p*')

# Configuration - Production Ready
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'voice_samples')
ATTENDANCE_FILE = os.environ.get('ATTENDANCE_FILE', 'attendance_records.json')
VOICE_MODELS_FILE = os.environ.get('VOICE_MODELS_FILE', 'voice_models.pkl')
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'webm'}

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

class VoiceRecognitionSystem:
    def __init__(self):
        self.voice_models = self.load_voice_models()
        self.attendance_records = self.load_attendance_records()
    
    def extract_voice_features(self, audio_file):
        """Extract MFCC features from audio file"""
        try:
            print(f"🎤 Starting voice feature extraction from: {audio_file}")
            
            # Load audio file
            y, sr = librosa.load(audio_file, sr=22050)
            print(f"📊 Audio loaded - Duration: {len(y)/sr:.2f}s, Sample Rate: {sr}Hz, Shape: {y.shape}")
            
            # Extract MFCC features
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            print(f"🔊 MFCC features extracted - Shape: {mfccs.shape}")
            
            # Calculate statistical features
            features = []
            for i in range(mfccs.shape[0]):
                features.extend([
                    np.mean(mfccs[i]),
                    np.std(mfccs[i]),
                    np.max(mfccs[i]),
                    np.min(mfccs[i])
                ])
            
            features_array = np.array(features)
            print(f"✅ Feature extraction successful - Feature vector size: {len(features_array)}")
            print(f"📈 Feature statistics - Min: {features_array.min():.4f}, Max: {features_array.max():.4f}, Mean: {features_array.mean():.4f}")
            
            return features_array
        except Exception as e:
            print(f"❌ Error extracting features: {e}")
            return None
    
    def enroll_student(self, student_id, student_name, audio_file):
        """Enroll a new student with their voice sample"""
        print(f"🎓 Starting enrollment for Student ID: {student_id}, Name: {student_name}")
        
        features = self.extract_voice_features(audio_file)
        if features is None:
            print(f"❌ Enrollment failed - Could not extract voice features")
            return False, "Failed to extract voice features"
        
        # Check if student already exists
        if student_id in self.voice_models:
            print(f"⚠️ Enrollment failed - Student ID '{student_id}' already exists")
            return False, "Student ID already exists"
        
        # Store voice model
        self.voice_models[student_id] = {
            'name': student_name,
            'features': features.tolist(),
            'enrollment_date': datetime.now().isoformat()
        }
        
        # Save to file
        self.save_voice_models()
        
        print(f"✅ Student '{student_name}' enrolled successfully!")
        print(f"📚 Total enrolled students: {len(self.voice_models)}")
        print(f"💾 Voice model saved to: {VOICE_MODELS_FILE}")
        
        return True, "Student enrolled successfully"
    
    def verify_student(self, student_id, audio_file, threshold=0.85):
        """Verify student identity using voice comparison"""
        print(f"🔍 Starting voice verification for Student ID: {student_id}")
        
        if student_id not in self.voice_models:
            print(f"❌ Verification failed - Student '{student_id}' not found in database")
            print(f"📚 Available students: {list(self.voice_models.keys())}")
            return False, "Student not found in database"
        
        # Extract features from provided audio
        print(f"🎤 Extracting features from test audio...")
        test_features = self.extract_voice_features(audio_file)
        if test_features is None:
            print(f"❌ Verification failed - Could not extract features from test audio")
            return False, "Failed to extract voice features"
        
        # Get stored features
        stored_features = np.array(self.voice_models[student_id]['features'])
        print(f"📊 Comparing features - Test: {len(test_features)}, Stored: {len(stored_features)}")
        
        # Calculate similarity
        similarity = cosine_similarity([test_features], [stored_features])[0][0]
        
        print(f"🎯 Voice similarity score: {similarity:.4f} (threshold: {threshold})")
        
        if similarity >= threshold:
            print(f"✅ Voice verification PASSED - {self.voice_models[student_id]['name']}")
            return True, f"Voice verified (similarity: {similarity:.2f})"
        else:
            print(f"❌ Voice verification FAILED - Similarity too low")
            return False, f"Voice verification failed (similarity: {similarity:.2f})"
    
    def mark_attendance(self, student_id, audio_file):
        """Mark attendance for a student after voice verification"""
        verified, message = self.verify_student(student_id, audio_file)
        
        if not verified:
            return False, message
        
        student_name = self.voice_models[student_id]['name']
        today = datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.now().isoformat()
        
        # Check if already marked today
        if today in self.attendance_records:
            if student_id in self.attendance_records[today]:
                return False, "Attendance already marked for today"
        else:
            self.attendance_records[today] = {}
        
        # Mark attendance
        self.attendance_records[today][student_id] = {
            'name': student_name,
            'timestamp': timestamp,
            'status': 'present'
        }
        
        self.save_attendance_records()
        return True, f"Attendance marked successfully for {student_name}"
    
    def get_attendance_report(self, date=None):
        """Get attendance report for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        return self.attendance_records.get(date, {})
    
    def get_all_students(self):
        """Get list of all enrolled students"""
        return {sid: data['name'] for sid, data in self.voice_models.items()}
    
    def load_voice_models(self):
        """Load voice models from file"""
        try:
            with open(VOICE_MODELS_FILE, 'rb') as f:
                models = pickle.load(f)
            print(f"📂 Voice models loaded successfully from {VOICE_MODELS_FILE}")
            print(f"👥 Loaded {len(models)} student voice models")
            return models
        except FileNotFoundError:
            print(f"📂 No existing voice models found. Starting with empty database.")
            return {}
        except Exception as e:
            print(f"❌ Error loading voice models: {e}")
            return {}
    
    def save_voice_models(self):
        """Save voice models to file"""
        try:
            with open(VOICE_MODELS_FILE, 'wb') as f:
                pickle.dump(self.voice_models, f)
            print(f"💾 Voice models saved successfully to {VOICE_MODELS_FILE}")
            print(f"📊 Saved {len(self.voice_models)} student voice models")
        except Exception as e:
            print(f"❌ Error saving voice models: {e}")
    
    def load_attendance_records(self):
        """Load attendance records from file"""
        try:
            with open(ATTENDANCE_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_attendance_records(self):
        """Save attendance records to file"""
        with open(ATTENDANCE_FILE, 'w') as f:
            json.dump(self.attendance_records, f, indent=2)

# Initialize the voice recognition system
voice_system = VoiceRecognitionSystem()

def allowed_file(filename):
    if not filename:
        return True  # Allow files without names (like recorded blobs)
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Main dashboard"""
    students = voice_system.get_all_students()
    today_attendance = voice_system.get_attendance_report()
    return render_template('index.html', students=students, attendance=today_attendance)

@app.route('/enroll')
def enroll_page():
    """Student enrollment page"""
    return render_template('enroll.html')
@app.route('/enroll_student', methods=['POST'])
def enroll_student():
    """Handle student enrollment"""
    try:
        student_id = request.form.get('student_id')
        student_name = request.form.get('student_name')
        print(f"Enrolling student: {student_id}, Name: {student_name}")
        
        if not student_id or not student_name:
            return jsonify({'success': False, 'message': 'Student ID and name are required'}), 400
        
        # Check for recorded audio first, then uploaded file
        audio_file = None
        if 'recorded_audio' in request.files and request.files['recorded_audio'].filename:
            audio_file = request.files['recorded_audio']
            print(f"Using recorded audio: {audio_file.filename}")
        elif 'voice_sample' in request.files and request.files['voice_sample'].filename:
            audio_file = request.files['voice_sample']
            print(f"Using uploaded file: {audio_file.filename}")
        
        if not audio_file:
            return jsonify({'success': False, 'message': 'No voice sample provided'}), 400
        
        if audio_file and allowed_file(audio_file.filename):
            print(f"Received file: {audio_file.filename}")
            
            # Generate filename based on file type
            file_ext = 'wav'
            if audio_file.filename and '.' in audio_file.filename:
                file_ext = audio_file.filename.rsplit('.', 1)[1].lower()
            
            filename = secure_filename(f"{student_id}_enrollment.{file_ext}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(filepath)
            
            success, message = voice_system.enroll_student(student_id, student_name, filepath)
            
            # Clean up temporary file
            try:
                os.remove(filepath)
            except OSError:
                pass
            
            return jsonify({
                'success': success,
                'message': message if success else f'Enrollment failed: {message}'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Invalid file format. Please upload WAV, MP3, FLAC, M4A, or WebM files.'
            }), 400
    
    except Exception as e:
        print(f"Error in enroll_student: {e}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500


@app.route('/attendance')
def attendance_page():
    """Attendance marking page"""
    students = voice_system.get_all_students()
    return render_template('attendance.html', students=students)

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    """Handle attendance marking"""
    try:
        print(f"🔍 Mark attendance request received")
        print(f"📝 Form data: {dict(request.form)}")
        print(f"📁 Files: {list(request.files.keys())}")
        
        student_id = request.form.get('student_id')
        print(f"👤 Student ID: {student_id}")
       
        if not student_id:
            return jsonify({'success': False, 'message': 'Please select a student'}), 400
        
        # Check for recorded audio first, then uploaded file
        audio_file = None
        if 'recorded_audio' in request.files and request.files['recorded_audio'].filename:
            audio_file = request.files['recorded_audio']
            print(f"Using recorded audio: {audio_file.filename}")
        elif 'voice_sample' in request.files and request.files['voice_sample'].filename:
            audio_file = request.files['voice_sample']
            print(f"Using uploaded file: {audio_file.filename}")
        
        if not audio_file:
            return jsonify({'success': False, 'message': 'No voice sample provided'}), 400
        
        if audio_file and allowed_file(audio_file.filename):
            
            file_ext = 'wav'
            if audio_file.filename and '.' in audio_file.filename:
                file_ext = audio_file.filename.rsplit('.', 1)[1].lower()
            
            filename = secure_filename(f"{student_id}_attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            audio_file.save(filepath)
            
            success, message = voice_system.mark_attendance(student_id, filepath)
            
            # Clean up temporary file
            try:
                os.remove(filepath)
            except OSError:
                pass
            
            return jsonify({'success': success, 'message': message})
        else:
            return jsonify({
                'success': False, 
                'message': 'Invalid file format. Please upload WAV, MP3, FLAC, M4A, or WebM files.'
            }), 400
    
    except Exception as e:
        print(f"Error in mark_attendance: {e}")
        return jsonify({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }), 500
@app.route('/reports')
def reports_page():
    """Attendance reports page"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    attendance = voice_system.get_attendance_report(date)
    all_students = voice_system.get_all_students()
    return render_template('reports.html', attendance=attendance, date=date, all_students=all_students)

@app.route('/api/verify_voice', methods=['POST'])
def api_verify_voice():
    """API endpoint for voice verification"""
    data = request.get_json()
    student_id = data.get('student_id')

    return jsonify({'status': 'success', 'message': 'API endpoint ready'})

@app.route('/api/system_status')
def system_status():
    """API endpoint to check system status and voice models"""
    try:
        students = voice_system.get_all_students()
        attendance_today = voice_system.get_attendance_report()
        
        # Check if files exist
        voice_models_exists = os.path.exists(VOICE_MODELS_FILE)
        attendance_file_exists = os.path.exists(ATTENDANCE_FILE)
        voice_samples_dir_exists = os.path.exists(UPLOAD_FOLDER)
        
        # Get file sizes if they exist
        voice_models_size = os.path.getsize(VOICE_MODELS_FILE) if voice_models_exists else 0
        attendance_file_size = os.path.getsize(ATTENDANCE_FILE) if attendance_file_exists else 0
        
        status = {
            'system_ready': True,
            'enrolled_students': len(students),
            'students_list': students,
            'attendance_today': len(attendance_today),
            'files': {
                'voice_models': {
                    'exists': voice_models_exists,
                    'path': VOICE_MODELS_FILE,
                    'size_bytes': voice_models_size
                },
                'attendance_records': {
                    'exists': attendance_file_exists,
                    'path': ATTENDANCE_FILE,
                    'size_bytes': attendance_file_size
                },
                'voice_samples_dir': {
                    'exists': voice_samples_dir_exists,
                    'path': UPLOAD_FOLDER
                }
            },
            'configuration': {
                'allowed_extensions': list(ALLOWED_EXTENSIONS),
                'max_file_size_mb': app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024),
                'upload_folder': UPLOAD_FOLDER
            }
        }
        
        return jsonify(status)
    
    except Exception as e:
        return jsonify({
            'system_ready': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Development vs Production
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1' if debug_mode else '0.0.0.0')
    
    app.run(debug=debug_mode, host=host, port=port)