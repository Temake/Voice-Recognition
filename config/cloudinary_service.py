import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import os
from datetime import datetime
import tempfile

class CloudinaryService:
    """Service for handling Cloudinary uploads and management"""
    
    def __init__(self):
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
            api_key=os.environ.get('CLOUDINARY_API_KEY'),
            api_secret=os.environ.get('CLOUDINARY_API_SECRET')
        )
    
    def upload_voice_sample(self, file_path, student_id, teacher_id, purpose='enrollment'):
        """
        Upload voice sample to Cloudinary
        
        Args:
            file_path: Path to the audio file
            student_id: Student identifier
            teacher_id: Teacher identifier
            purpose: 'enrollment' or 'attendance'
        
        Returns:
            dict: Upload result with url and public_id
        """
        try:
            # Check if Cloudinary is enabled
            use_cloudinary = os.environ.get('USE_CLOUDINARY', 'true').lower() == 'true'
            if not use_cloudinary:
                print("🏠 Cloudinary disabled - using local storage")
                return {
                    'success': False,
                    'error': 'Cloudinary disabled in configuration',
                    'fallback': True
                }
            
            print(f"🌤️ Uploading to Cloudinary: {file_path}")
            
            # Check if Cloudinary is configured
            cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
            api_key = os.environ.get('CLOUDINARY_API_KEY') 
            api_secret = os.environ.get('CLOUDINARY_API_SECRET')
            
            if not all([cloud_name, api_key, api_secret]):
                print("⚠️ Cloudinary not configured - falling back to local storage")
                return {
                    'success': False,
                    'error': 'Cloudinary not configured',
                    'fallback': True
                }
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            public_id = f"voice_samples/{teacher_id}/{student_id}_{purpose}_{timestamp}"
            
            print(f"📤 Uploading to Cloudinary with public_id: {public_id}")
            
            # Upload with audio resource type
            result = cloudinary.uploader.upload(
                file_path,
                resource_type="video",  # Use video for audio files
                public_id=public_id,
                folder=f"voice_attendance/teacher_{teacher_id}",
                tags=[f"teacher_{teacher_id}", f"student_{student_id}", purpose],
                context={
                    "student_id": student_id,
                    "teacher_id": teacher_id,
                    "purpose": purpose,
                    "uploaded_at": timestamp
                }
            )
            
            print(f"✅ Cloudinary upload successful: {result['secure_url']}")
            
            return {
                'success': True,
                'url': result['secure_url'],
                'public_id': result['public_id'],
                'format': result.get('format', 'unknown')
            }
            
        except Exception as e:
            print(f"❌ Cloudinary upload error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback': True
            }
    
    def delete_voice_sample(self, public_id):
        """Delete voice sample from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type="video")
            return result.get('result') == 'ok'
        except Exception as e:
            print(f"❌ Cloudinary delete error: {str(e)}")
            return False
    
    def get_voice_sample_url(self, public_id, transformation=None):
        """Get optimized URL for voice sample"""
        try:
            if transformation:
                url, _ = cloudinary_url(public_id, resource_type="video", **transformation)
            else:
                url, _ = cloudinary_url(public_id, resource_type="video")
            return url
        except Exception as e:
            print(f"❌ Cloudinary URL generation error: {str(e)}")
            return None
    
    def cleanup_teacher_files(self, teacher_id):
        """Clean up all files for a teacher (when account is deleted)"""
        try:
            # Delete all files in teacher's folder
            result = cloudinary.api.delete_resources_by_prefix(
                f"voice_attendance/teacher_{teacher_id}",
                resource_type="video"
            )
            return result
        except Exception as e:
            print(f"❌ Cloudinary cleanup error: {str(e)}")
            return False
    
    def save_temp_file(self, audio_file):
        """Save uploaded file to temporary location"""
        try:
            # Create temporary file
            suffix = '.wav'
            if audio_file.filename and '.' in audio_file.filename:
                suffix = '.' + audio_file.filename.rsplit('.', 1)[1].lower()
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            audio_file.save(temp_file.name)
            temp_file.close()
            
            return temp_file.name
        except Exception as e:
            print(f"❌ Temp file save error: {str(e)}")
            return None
    
    def cleanup_temp_file(self, file_path):
        """Remove temporary file"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                print(f"🗑️ Cleaned up temp file: {os.path.basename(file_path)}")
                return True
        except Exception as e:
            print(f"❌ Temp file cleanup error: {str(e)}")
            return False

# Global instance
cloudinary_service = CloudinaryService()
