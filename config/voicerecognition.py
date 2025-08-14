from flask import current_app

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







os.makedirs(UPLOAD_FOLDER, exist_ok=True)




class EnhancedVoiceRecognitionSystem:
    def __init__(self):
        self.voice_models = self.load_voice_models()
        self.attendance_records = self.load_attendance_records()
        self.security_manager = SecurityManager()
    
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
    
    def enroll_student(self, student_id, student_name, audio_file):
        """Enroll a new student with enhanced security"""
        print(f"🎓 Starting enhanced enrollment for Student ID: {student_id}, Name: {student_name}")
        
        # Check if student already exists
        if student_id in self.voice_models:
            self.security_manager.log_security_event(
                "DUPLICATE_ENROLLMENT_ATTEMPT", 
                student_id, 
                f"Attempted to re-enroll existing student: {student_name}"
            )
            return False, "Student ID already exists"
        
        # Convert audio if needed
        audio = self.convert_m4a_to_wav(audio_file) if audio_file.endswith('.m4a') else audio_file
        
        # Extract enhanced features
        features, message = self.extract_enhanced_voice_features(audio)
        if features is None:
            self.security_manager.log_security_event(
                "ENROLLMENT_FEATURE_EXTRACTION_FAILED", 
                student_id, 
                f"Feature extraction failed: {message}"
            )
            return False, f"Enrollment failed: {message}"
        
        # Store voice model with metadata
        enrollment_hash = hashlib.sha256(f"{student_id}{student_name}{datetime.datetime.now().isoformat()}".encode()).hexdigest()
        
        self.voice_models[student_id] = {
            'name': student_name,
            'features': features.tolist(),
            'enrollment_date': datetime.datetime.now().isoformat(),
            'enrollment_hash': enrollment_hash,
            'feature_version': '2.0',  # Version tracking
            'verification_count': 0
        }
        
        # Save to file
        self.save_voice_models()
        
        # Log successful enrollment
        self.security_manager.log_security_event(
            "SUCCESSFUL_ENROLLMENT", 
            student_id, 
            f"Student {student_name} enrolled successfully with enhanced features"
        )
        
        print(f"✅ Student '{student_name}' enrolled successfully with enhanced security!")
        return True, "Student enrolled successfully"
    
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
            return True, f"Voice verified for {student_name} (confidence: {combined_similarity:.2f})", combined_similarity
        else:
            # Record failed attempt
            self.security_manager.record_failed_attempt(student_id)
            self.security_manager.log_security_event(
                "FAILED_VOICE_VERIFICATION", 
                student_id, 
                f"Voice verification failed for {student_name} (similarity: {combined_similarity:.4f})"
            )
            
            print(f"❌ Voice verification FAILED - Similarity too low")
            return False, f"Voice verification failed (confidence: {combined_similarity:.2f})", combined_similarity
    
    def mark_attendance(self, student_id, audio_file):
        """Enhanced attendance marking with comprehensive security"""
        print(f"📝 Starting enhanced attendance marking for Student ID: {student_id}")
        
        # Rate limiting check
        rate_limit_key = f"attendance_{student_id}"
        if not self.security_manager.check_rate_limit(rate_limit_key):
            self.security_manager.log_security_event(
                "RATE_LIMIT_EXCEEDED", 
                student_id, 
                "Rate limit exceeded for attendance marking"
            )
            return False, "Too many attendance attempts. Please wait before trying again."
        
        # Verify voice with enhanced security
        verified, message, similarity = self.verify_student_voice(student_id, audio_file)
        
        if not verified:
            self.security_manager.apply_rate_limit(rate_limit_key)
            return False, message
        
        student_name = self.voice_models[student_id]['name']
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        timestamp = datetime.datetime.now().isoformat()
        
        # Check if already marked today
        if today in self.attendance_records:
            if student_id in self.attendance_records[today]:
                self.security_manager.log_security_event(
                    "DUPLICATE_ATTENDANCE_ATTEMPT", 
                    student_id, 
                    f"Attempted to mark attendance twice for {student_name}"
                )
                return False, "Attendance already marked for today"
        else:
            self.attendance_records[today] = {}
        
        # Mark attendance with enhanced metadata
        self.attendance_records[today][student_id] = {
            'name': student_name,
            'timestamp': timestamp,
            'status': 'present',
            'verification_similarity': similarity,
            'verification_method': 'enhanced_voice_v2.0'
        }
        
        self.save_attendance_records()
        
        # Log successful attendance
        self.security_manager.log_security_event(
            "SUCCESSFUL_ATTENDANCE", 
            student_id, 
            f"Attendance marked for {student_name} (similarity: {similarity:.4f})"
        )
        
        print(f"✅ Attendance marked successfully for {student_name}")
        return True, f"Attendance marked successfully for {student_name}"
    
    def get_attendance_report(self, date=None):
        """Get attendance report for a specific date"""
        if date is None:
            date = datetime.datetime.now().strftime('%Y-%m-%d')
        return self.attendance_records.get(date, {})
    
    def get_all_students(self):
        """Get list of all enrolled students"""
        return {sid: data['name'] for sid, data in self.voice_models.items()}
    
    def get_security_report(self, days=7):
        """Get security report for the last N days"""
        cutoff_date = datetime.datetime.now().timestamp() - (days * 24 * 60 * 60)
        recent_events = [
            event for event in self.security_manager.security_log 
            if datetime.datetime.fromisoformat(event['timestamp']).timestamp() > cutoff_date
        ]
        return recent_events
    
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