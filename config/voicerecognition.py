from flask import current_app
from flask_login import current_user

import json 
import hashlib
import os
from .constants import *
import librosa
from pydub import AudioSegment
import soundfile as sf
from sklearn.metrics.pairwise import cosine_similarity
from werkzeug.utils import secure_filename
import pickle
import datetime
import numpy as np
from .security import SecurityManager
from .models import db, Student, AttendanceRecord, SecurityLog
from .cloudinary_service import cloudinary_service







os.makedirs(UPLOAD_FOLDER, exist_ok=True)




class EnhancedVoiceRecognitionSystem:
    def __init__(self):
        # Legacy support - load existing data on first run
        self.legacy_voice_models = self.load_legacy_voice_models()
        self.legacy_attendance_records = self.load_legacy_attendance_records()
        self.security_manager = SecurityManager()
        
        # Migrate legacy data if needed
        self.migrate_legacy_data_if_needed()
    
    def migrate_legacy_data_if_needed(self):
        """Migrate legacy pickle data to database if needed"""
        try:
            # Check if current_user is available and authenticated
            has_authenticated_user = (
                current_user and 
                hasattr(current_user, 'is_authenticated') and 
                current_user.is_authenticated and
                hasattr(current_user, 'id')
            )
            
            if self.legacy_voice_models and has_authenticated_user:
                print("🔄 Starting legacy data migration...")
                migrated = 0
                
                for student_id, data in self.legacy_voice_models.items():
                    # Check if student already exists in DB
                    existing = Student.query.filter_by(
                        student_id=student_id, 
                        teacher_id=current_user.id
                    ).first()
                    
                    if not existing:
                        student = Student(
                            student_id=student_id,
                            student_name=data.get('name', f'Student {student_id}'),
                            teacher_id=current_user.id
                        )
                        student.set_voice_features(data.get('features', []))
                        db.session.add(student)
                        migrated += 1
                
                if migrated > 0:
                    db.session.commit()
                    print(f"✅ Migrated {migrated} students to database")
                
                # Migrate attendance records
                att_migrated = 0
                if self.legacy_attendance_records:
                    for record in self.legacy_attendance_records:
                        # Find corresponding student
                        student = Student.query.filter_by(
                            student_id=record.get('student_id'),
                            teacher_id=current_user.id
                        ).first()
                        
                        if student:
                            att_record = AttendanceRecord(
                                student_id=student.id,
                                teacher_id=current_user.id,
                                timestamp=datetime.datetime.fromisoformat(record.get('timestamp')),
                                confidence_score=record.get('confidence', 0.0)
                            )
                            db.session.add(att_record)
                            att_migrated += 1
                    
                    if att_migrated > 0:
                        db.session.commit()
                        print(f"✅ Migrated {att_migrated} attendance records to database")
            
            elif self.legacy_voice_models:
                print("ℹ️ Legacy data found but no authenticated user - migration will occur on first login")
                        
        except Exception as e:
            print(f"⚠️ Legacy migration warning: {e}")
            # Don't fail the initialization, just log the warning
    
    def load_legacy_voice_models(self):
        """Load legacy voice models from pickle file"""
        try:
            if os.path.exists(VOICE_MODELS_FILE):
                with open(VOICE_MODELS_FILE, 'rb') as f:
                    models = pickle.load(f)
                print(f"📂 Legacy voice models loaded: {len(models)} students")
                return models
        except Exception as e:
            print(f"📂 No legacy voice models found: {e}")
        return {}
    
    def load_legacy_attendance_records(self):
        """Load legacy attendance records from JSON file"""
        try:
            if os.path.exists(ATTENDANCE_FILE):
                with open(ATTENDANCE_FILE, 'r') as f:
                    records = json.load(f)
                print(f"📂 Legacy attendance records loaded: {len(records)} records")
                return records
        except Exception as e:
            print(f"📂 No legacy attendance records found: {e}")
        return []
    
    def validate_audio_file(self, audio_file_path):
        """Validate audio file quality and properties"""
        try:
            y, sr = librosa.load(audio_file_path, sr=None)
            duration = len(y) / sr
            
            # Check duration
            if duration < MIN_AUDIO_DURATION:
                return False, f"Audio too short. Minimum {MIN_AUDIO_DURATION} seconds required."
            
            if duration > MAX_AUDIO_DURATION:
                return False, f"Audio too long. Maximum {MAX_AUDIO_DURATION} seconds allowed."
            
            # Check for silence (basic voice activity detection)
            energy = np.sqrt(np.mean(y**2))
            if energy < 0.001:  # Threshold for silence detection
                return False, "Audio appears to be silent or too quiet."
            
            # Check for minimum frequency content (basic voice detection)
            fft = np.fft.fft(y)
            freq_energy = np.abs(fft)
            
            # Look for voice-like frequency content (roughly 85Hz - 8kHz)
            voice_range_start = int(85 * len(fft) / sr)
            voice_range_end = int(8000 * len(fft) / sr)
            voice_energy = np.sum(freq_energy[voice_range_start:voice_range_end])
            total_energy = np.sum(freq_energy)
            
            if voice_energy / total_energy < 0.1:  # At least 10% energy in voice range
                return False, "Audio doesn't appear to contain voice content."
            
            print(f"✅ Audio validation passed: Duration {duration:.2f}s, Energy: {energy:.4f}")
            return True, "Audio validation successful"
            
        except Exception as e:
            return False, f"Error processing audio file: {str(e)}"
            voice_freq_range = freq_energy[int(len(freq_energy) * 85/sr):int(len(freq_energy) * 3400/sr)]
            
            if np.mean(voice_freq_range) < np.mean(freq_energy) * 0.1:
                return False, "Audio doesn't appear to contain human voice."
            
            return True, "Audio validation passed"
            
        except Exception as e:
            return False, f"Audio validation error: {str(e)}"
    
    def extract_enhanced_voice_features(self, audio_file):
        """Extract enhanced voice features with additional security measures"""
        try:
            print(f"🎤 Starting enhanced voice feature extraction from: {audio_file}")
            
            # Validate audio first
            valid, validation_message = self.validate_audio_file(audio_file)
            if not valid:
                print(f"❌ Audio validation failed: {validation_message}")
                return None, validation_message
            
            y, sr = librosa.load(audio_file, sr=22050)  # Standardize sample rate
            print(f"📊 Audio loaded - Duration: {len(y)/sr:.2f}s, Sample Rate: {sr}Hz")
            
            # Extract multiple types of features for better discrimination
            features = []
            
            # 1. MFCC features (spectral characteristics)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            for i in range(mfccs.shape[0]):
                features.extend([
                    np.mean(mfccs[i]),
                    np.std(mfccs[i]),
                    np.max(mfccs[i]),
                    np.min(mfccs[i])
                ])
            
            # 2. Pitch/F0 features (fundamental frequency)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                features.extend([
                    np.mean(pitch_values),
                    np.std(pitch_values),
                    np.max(pitch_values),
                    np.min(pitch_values)
                ])
            else:
                features.extend([0, 0, 0, 0])
            
            # 3. Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            
            features.extend([
                np.mean(spectral_centroids),
                np.std(spectral_centroids),
                np.mean(spectral_rolloff),
                np.std(spectral_rolloff)
            ])
            
            # 4. Formant-like features (approximation)
            stft = librosa.stft(y)
            magnitude = np.abs(stft)
            formant_features = []
            for frame in range(min(10, magnitude.shape[1])):  # Sample first 10 frames
                frame_mag = magnitude[:, frame]
                peaks = np.where(frame_mag > np.mean(frame_mag) + np.std(frame_mag))[0]
                if len(peaks) >= 2:
                    formant_features.extend([peaks[0], peaks[1]])
                else:
                    formant_features.extend([0, 0])
            
            # Pad or truncate to fixed size
            while len(formant_features) < 20:
                formant_features.append(0)
            formant_features = formant_features[:20]
            features.extend(formant_features)
            
            features_array = np.array(features)
            
            # Normalize features
            if np.std(features_array) != 0:
                features_array = (features_array - np.mean(features_array)) / np.std(features_array)
            
            print(f"✅ Enhanced feature extraction successful - Feature vector size: {len(features_array)}")
            return features_array, "Feature extraction successful"
            
        except Exception as e:
            error_msg = f"Error extracting enhanced features: {e}"
            print(f"❌ {error_msg}")
            return None, error_msg
    
    def convert_m4a_to_wav(self, input_m4a_path):
        try:
            print(f"🔄 Converting M4A to WAV: {input_m4a_path}")
            
            audio = AudioSegment.from_file(input_m4a_path, format="m4a")
            output_wav_path = input_m4a_path.rsplit('.', 1)[0] + '.wav'
            audio.export(output_wav_path, format="wav")
            
            print(f"✅ Conversion successful: {output_wav_path}")
            return output_wav_path
            
        except Exception as e:
            print(f"❌ Error converting M4A to WAV: {e}")
            return None
    
    def enroll_student(self, student_id, student_name, audio_file_path):
        """Enhanced student enrollment with database and Cloudinary"""
        try:
            # Check if current_user is available and authenticated
            if not (current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated):
                return False, "Authentication required for enrollment"
            
            print(f"🎓 Starting enrollment for Student ID: {student_id}, Name: {student_name}")
            
            # Check if student already exists for this teacher
            existing_student = Student.query.filter_by(
                student_id=student_id, 
                teacher_id=current_user.id
            ).first()
            
            if existing_student:
                return False, f"Student {student_id} is already enrolled"
            
            # Validate audio file
            is_valid, validation_message = self.validate_audio_file(audio_file_path)
            if not is_valid:
                return False, f"Audio validation failed: {validation_message}"
            
            # Extract voice features  
            features, message = self.extract_enhanced_voice_features(audio_file_path)
            if features is None:
                self.security_manager.log_security_event(
                    "ENROLLMENT_FEATURE_EXTRACTION_FAILED", 
                    student_id, 
                    f"Feature extraction failed: {message}",
                    teacher_id=current_user.id
                )
                return False, f"Enrollment failed: {message}"
            
            # Upload to Cloudinary (with fallback to local storage)
            upload_result = cloudinary_service.upload_voice_sample(
                audio_file_path, 
                student_id, 
                current_user.id, 
                'enrollment'
            )
            
            voice_sample_url = None
            if upload_result['success']:
                voice_sample_url = upload_result['url']
                print(f"✅ Voice sample uploaded to Cloudinary")
            else:
                print(f"⚠️ Cloudinary upload failed: {upload_result.get('error', 'Unknown error')}")
                print(f"📁 Voice features will be stored without cloud URL")
                # We can still proceed without the cloud URL since we have the features
            
            # Create student record
            student = Student(
                student_id=student_id,
                student_name=student_name,
                teacher_id=current_user.id,
                voice_sample_url=voice_sample_url  # Will be None if Cloudinary failed
            )
            student.set_voice_features(features)
            
            # Save to database
            db.session.add(student)
            db.session.commit()
            
            # Log successful enrollment
            self.security_manager.log_security_event(
                "SUCCESSFUL_ENROLLMENT", 
                student_id, 
                f"Student {student_name} enrolled successfully",
                teacher_id=current_user.id
            )
            
            print(f"✅ Student '{student_name}' enrolled successfully!")
            return True, "Student enrolled successfully"
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Enrollment error: {e}")
            return False, f"Enrollment failed: {str(e)}"
    
    def verify_student_voice(self, student_id, audio_file, threshold=MIN_VOICE_THRESHOLD):
        """Enhanced voice verification with security measures"""
        print(f"🔍 Starting enhanced voice verification for Student ID: {student_id}")
        
        # Check if student exists
        if student_id not in self.voice_models:
            self.security_manager.log_security_event(
                "VERIFICATION_UNKNOWN_STUDENT", 
                student_id, 
                "Attempted verification for unknown student ID"
            )
            return False, "Student not found in database", 0.0
        
        # Check for suspicious activity
        if self.security_manager.check_suspicious_activity(student_id):
            self.security_manager.log_security_event(
                "SUSPICIOUS_ACTIVITY_DETECTED", 
                student_id, 
                "Multiple failed verification attempts detected"
            )
            return False, "Account temporarily locked due to suspicious activity", 0.0
        
        # Convert audio if needed
        audio = self.convert_m4a_to_wav(audio_file) if audio_file.endswith('.m4a') else audio_file
        
        # Extract features from test audio
        test_features, message = self.extract_enhanced_voice_features(audio)
        if test_features is None:
            self.security_manager.record_failed_attempt(student_id)
            self.security_manager.log_security_event(
                "VERIFICATION_FEATURE_EXTRACTION_FAILED", 
                student_id, 
                f"Feature extraction failed during verification: {message}"
            )
            return False, f"Verification failed: {message}", 0.0
        
        # Get stored features
        stored_features = np.array(self.voice_models[student_id]['features'])
        
        # Verify feature compatibility
        if len(test_features) != len(stored_features):
            self.security_manager.record_failed_attempt(student_id)
            self.security_manager.log_security_event(
                "FEATURE_DIMENSION_MISMATCH", 
                student_id, 
                f"Feature dimensions don't match: {len(test_features)} vs {len(stored_features)}"
            )
            return False, "Feature extraction error - please try again", 0.0
        
        # Calculate similarity using multiple methods
        cosine_sim = cosine_similarity([test_features], [stored_features])[0][0]
        
        # Additional similarity measures for enhanced security
        euclidean_dist = np.linalg.norm(test_features - stored_features)
        normalized_euclidean = 1 / (1 + euclidean_dist)  # Convert distance to similarity
        
        # Weighted combination of similarities
        combined_similarity = 0.7 * cosine_sim + 0.3 * normalized_euclidean
        
        print(f"🎯 Voice similarity analysis:")
        print(f"   Cosine similarity: {cosine_sim:.4f}")
        print(f"   Euclidean similarity: {normalized_euclidean:.4f}")
        print(f"   Combined similarity: {combined_similarity:.4f}")
        print(f"   Threshold: {threshold}")
        
        student_name = self.voice_models[student_id]['name']
        
        if combined_similarity >= threshold:
            # Update verification count
            self.voice_models[student_id]['verification_count'] += 1
            self.voice_models[student_id]['last_verification'] = datetime.datetime.now().isoformat()
            self.save_voice_models()
            
            self.security_manager.log_security_event(
                "SUCCESSFUL_VOICE_VERIFICATION", 
                student_id, 
                f"Voice verified for {student_name} (similarity: {combined_similarity:.4f})"
            )
            
            print(f"✅ Voice verification PASSED - {student_name}")
            return True, f"Voice verified for {student_name} (confidence: {combined_similarity:.2f})", float(combined_similarity)
        else:
            # Record failed attempt
            self.security_manager.record_failed_attempt(student_id)
            self.security_manager.log_security_event(
                "FAILED_VOICE_VERIFICATION", 
                student_id, 
                f"Voice verification failed for {student_name} (similarity: {combined_similarity:.4f})"
            )
            
            print(f"❌ Voice verification FAILED - Similarity too low")
            return False, f"Voice verification failed (confidence: {combined_similarity:.2f})", float(combined_similarity)
    
    def mark_attendance(self, student_id, audio_file_path):
        """Enhanced attendance marking with database and Cloudinary"""
        try:
            # Check if current_user is available and authenticated
            if not (current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated):
                return False, "Authentication required for attendance"
                
            print(f"📝 Starting attendance marking for Student ID: {student_id}")
            
            # Find student
            student = Student.query.filter_by(
                student_id=student_id,
                teacher_id=current_user.id
            ).first()
            
            if not student:
                return False, f"Student {student_id} not found"
            
            # Check if already marked today
            today = datetime.datetime.now().date()
            existing_record = AttendanceRecord.query.filter(
                AttendanceRecord.student_id == student.id,
                db.func.date(AttendanceRecord.timestamp) == today
            ).first()
            
            if existing_record:
                self.security_manager.log_security_event(
                    "DUPLICATE_ATTENDANCE_ATTEMPT", 
                    student_id, 
                    f"Attempted to mark attendance twice for {student.student_name}",
                    teacher_id=current_user.id
                )
                return False, "Attendance already marked for today"
            
            # Rate limiting check
            rate_limit_key = f"attendance_{student_id}_{current_user.id}"
            if not self.security_manager.check_rate_limit(rate_limit_key):
                self.security_manager.log_security_event(
                    "RATE_LIMIT_EXCEEDED", 
                    student_id, 
                    "Rate limit exceeded for attendance marking",
                    teacher_id=current_user.id
                )
                return False, "Too many attendance attempts. Please wait before trying again."
            
            # Verify voice
            verified, message, similarity = self.verify_student_voice_db(student, audio_file_path)
            
            if not verified:
                self.security_manager.apply_rate_limit(rate_limit_key)
                return False, message
            
            # Upload attendance audio to Cloudinary
            upload_result = cloudinary_service.upload_voice_sample(
                audio_file_path, 
                student_id, 
                current_user.id, 
                'attendance'
            )
            
            # Create attendance record
            attendance_record = AttendanceRecord(
                student_id=student.id,
                teacher_id=current_user.id,
                confidence_score=float(similarity),  # Convert numpy float64 to Python float
                voice_sample_url=upload_result.get('url') if upload_result['success'] else None,
                ip_address=None  # Will be set by the route
            )
            
            db.session.add(attendance_record)
            db.session.commit()
            
            # Log successful attendance
            self.security_manager.log_security_event(
                "SUCCESSFUL_ATTENDANCE", 
                student_id, 
                f"Attendance marked for {student.student_name} (confidence: {similarity:.4f})",
                teacher_id=current_user.id
            )
            
            print(f"✅ Attendance marked successfully for {student.student_name}")
            return True, f"Attendance marked successfully for {student.student_name}"
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Attendance error: {e}")
            return False, f"Attendance marking failed: {str(e)}"
    
    def verify_student_voice_db(self, student, audio_file_path, threshold=MIN_VOICE_THRESHOLD):
        """Enhanced voice verification using database student record"""
        try:
            print(f"🔍 Starting voice verification for {student.student_name}")
            
            # Get stored features
            stored_features = student.get_voice_features()
            if not stored_features:
                return False, "No voice features found for student", 0.0
            
            # Extract features from test audio
            test_features, message = self.extract_enhanced_voice_features(audio_file_path)
            if test_features is None:
                self.security_manager.record_failed_attempt(student.student_id)
                self.security_manager.log_security_event(
                    "VERIFICATION_FEATURE_EXTRACTION_FAILED", 
                    student.student_id, 
                    f"Feature extraction failed during verification: {message}",
                    teacher_id=current_user.id
                )
                return False, f"Verification failed: {message}", 0.0
            
            # Convert stored features to numpy array
            stored_features = np.array(stored_features)
            
            # Verify feature compatibility
            if len(test_features) != len(stored_features):
                self.security_manager.record_failed_attempt(student.student_id)
                self.security_manager.log_security_event(
                    "FEATURE_DIMENSION_MISMATCH", 
                    student.student_id, 
                    f"Feature dimensions don't match: {len(test_features)} vs {len(stored_features)}",
                    teacher_id=current_user.id
                )
                return False, "Feature extraction error - please try again", 0.0
            
            # Calculate similarity using multiple methods
            cosine_sim = cosine_similarity([test_features], [stored_features])[0][0]
            
            # Additional similarity measures for enhanced security
            euclidean_dist = np.linalg.norm(test_features - stored_features)
            normalized_euclidean = 1 / (1 + euclidean_dist)  # Convert distance to similarity
            
            # Weighted combination of similarities
            combined_similarity = 0.7 * cosine_sim + 0.3 * normalized_euclidean
            
            print(f"🎯 Voice similarity analysis:")
            print(f"   Cosine similarity: {cosine_sim:.4f}")
            print(f"   Euclidean similarity: {normalized_euclidean:.4f}")
            print(f"   Combined similarity: {combined_similarity:.4f}")
            print(f"   Threshold: {threshold}")
            
            if combined_similarity >= threshold:
                self.security_manager.log_security_event(
                    "SUCCESSFUL_VOICE_VERIFICATION", 
                    student.student_id, 
                    f"Voice verified for {student.student_name} (similarity: {combined_similarity:.4f})",
                    teacher_id=current_user.id
                )
                print(f"✅ Voice verification SUCCESS - High similarity")
                return True, f"Voice verified successfully (confidence: {combined_similarity:.2f})", float(combined_similarity)
            else:
                self.security_manager.record_failed_attempt(student.student_id)
                self.security_manager.log_security_event(
                    "FAILED_VOICE_VERIFICATION", 
                    student.student_id, 
                    f"Voice verification failed for {student.student_name} (similarity: {combined_similarity:.4f})",
                    teacher_id=current_user.id
                )
                print(f"❌ Voice verification FAILED - Similarity too low")
                return False, f"Voice verification failed (confidence: {combined_similarity:.2f})", float(combined_similarity)
                
        except Exception as e:
            print(f"❌ Voice verification error: {e}")
            return False, f"Verification error: {str(e)}", 0.0
    
    def get_attendance_report(self, date=None):
        """Get attendance report from database"""
        try:
            # Check if current_user is available and authenticated
            if not (current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated):
                return []
            
            query = AttendanceRecord.query.filter_by(teacher_id=current_user.id)
            
            if date:
                # Parse date and filter
                target_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                query = query.filter(db.func.date(AttendanceRecord.timestamp) == target_date)
            else:
                # Default to today
                today = datetime.datetime.now().date()
                query = query.filter(db.func.date(AttendanceRecord.timestamp) == today)
            
            records = query.join(Student).all()
            
            # Format for compatibility with existing templates - return as dictionary
            attendance_data = {}
            for record in records:
                attendance_data[record.student.student_id] = {
                    'student_id': record.student.student_id,
                    'name': record.student.student_name,
                    'timestamp': record.timestamp.isoformat(),
                    'status': record.status,
                    'confidence': float(record.confidence_score)  # Convert to Python float
                }
            
            return attendance_data
            
        except Exception as e:
            print(f"❌ Error getting attendance report: {e}")
            return []
    
    def get_all_students(self):
        """Get all students for current teacher from database"""
        try:
            # Check if current_user is available and authenticated
            if not (current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated):
                return {}
            
            students = Student.query.filter_by(
                teacher_id=current_user.id, 
                is_active=True
            ).all()
            
            # Format for compatibility with existing templates
            return {student.student_id: student.student_name for student in students}
            
        except Exception as e:
            print(f"❌ Error getting students: {e}")
            return {}
    
    def get_security_report(self, days=7):
        """Get security report from database"""
        try:
            # Check if current_user is available and authenticated
            if not (current_user and hasattr(current_user, 'is_authenticated') and current_user.is_authenticated):
                return []
            
            # Calculate cutoff date
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            # Query security logs
            security_events = SecurityLog.query.filter(
                SecurityLog.teacher_id == current_user.id,
                SecurityLog.timestamp >= cutoff_date
            ).order_by(SecurityLog.timestamp.desc()).all()
            
            # Convert to dictionary format for compatibility
            return [event.to_dict() for event in security_events]
            
        except Exception as e:
            print(f"❌ Error getting security report: {e}")
            return []

    
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


voice_system = EnhancedVoiceRecognitionSystem()