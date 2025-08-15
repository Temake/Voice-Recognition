# Voice Attendance System - Enhanced with Authentication

## 🔥 New Features Added

### 🔐 Authentication System
- **Teacher Registration & Login**: Secure authentication for teachers
- **Role-based Access**: Students can only enroll, teachers can access all features
- **Isolated Data**: Each teacher has their own student database
- **Secure Sessions**: Flask-Login with password hashing

### ☁️ Cloud Storage Integration
- **Cloudinary Integration**: Voice samples stored securely in the cloud
- **Automatic Upload**: Voice samples uploaded during enrollment and attendance
- **Organized Storage**: Files organized by teacher and purpose
- **Backup Strategy**: Maintains compatibility with existing file-based system

### 🗄️ Database Migration
- **PostgreSQL Support**: Migrated from pickle files to PostgreSQL database
- **Data Models**: Proper relational database design
- **Legacy Support**: Automatic migration from existing pickle/JSON data
- **Scalable Design**: Support for multiple teachers and thousands of students

### 🔗 Student Enrollment Flow
1. **Teacher Registration**: Teachers register and login
2. **Share Link**: Teachers get unique enrollment links
3. **Student Enrollment**: Students use the link to enroll (no login required)
4. **Isolated Environment**: Each teacher's students are isolated

## 🚀 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Copy `env.example` to `.env` and configure:

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost:5432/voice_attendance

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
```

### 3. Database Setup
```bash
python migrate.py
```

### 4. Run Application
```bash
python app.py
```

## 🌊 Usage Flow

### For Teachers:
1. **Register**: Go to `/auth/register` to create teacher account
2. **Login**: Access `/auth/login` to sign in
3. **Get Share Link**: Click "Share Link" button in navigation
4. **Share with Students**: Give the enrollment link to students
5. **Manage System**: Access dashboard, reports, and security features

### For Students:
1. **Get Link**: Receive enrollment link from teacher
2. **Enroll**: Use the link to enroll with voice sample
3. **No Login Required**: Students don't need accounts

## 🔒 Security Features

- **Password Hashing**: Bcrypt password hashing
- **Rate Limiting**: Prevents abuse of enrollment/attendance endpoints
- **IP Tracking**: All activities logged with IP addresses
- **Suspicious Activity Detection**: Automatic detection of unusual patterns
- **Secure File Handling**: Temporary files cleaned up automatically

## 📊 Database Schema

### Teachers Table
- User authentication and profile information
- Each teacher has isolated student data

### Students Table
- Student enrollment information
- Voice features stored as JSON
- Linked to specific teacher

### Attendance Records Table
- Timestamped attendance records
- Confidence scores and voice sample URLs
- IP address logging

### Security Logs Table
- Comprehensive security event logging
- Teacher-specific security monitoring

## 🔄 Migration from Legacy System

The system automatically migrates existing data:
- **Pickle Files**: `voice_models.pkl` → Students table
- **JSON Files**: `attendance_records.json` → AttendanceRecord table
- **Security Logs**: Continues file-based logging as backup

## 🐳 Docker Support

Updated Docker configuration includes:
- PostgreSQL database service
- Environment variable support
- Volume mounting for data persistence
- Production-ready configuration

## 🎯 Key Benefits

1. **Multi-tenant**: Multiple teachers can use the same system
2. **Scalable**: PostgreSQL can handle thousands of users
3. **Secure**: Proper authentication and authorization
4. **Cloud-Ready**: Voice samples stored in Cloudinary
5. **User-Friendly**: Simple enrollment flow for students
6. **Maintainable**: Clean database design and code organization

## 📝 API Endpoints

### Public Endpoints
- `GET /` - Home page (redirects based on auth status)
- `GET /auth/login` - Teacher login page
- `GET /auth/register` - Teacher registration page
- `GET /enroll?teacher_id=X` - Student enrollment page
- `POST /enroll_student` - Student enrollment submission

### Protected Endpoints (Teachers Only)
- `GET /dashboard` - Teacher dashboard
- `GET /attendance` - Attendance marking page
- `GET /reports` - Attendance reports
- `GET /security` - Security dashboard
- `GET /share_link` - Get enrollment link
- `POST /mark_attendance` - Mark student attendance

## 🔧 Configuration Options

All configuration is through environment variables:
- Database connection settings
- Cloudinary API credentials
- Security thresholds and timeouts
- Audio processing parameters
- File upload limits

## 🚀 Production Deployment

1. Set up PostgreSQL database
2. Configure Cloudinary account
3. Set all environment variables
4. Run migration script
5. Deploy with proper WSGI server (Gunicorn)
6. Use reverse proxy (Nginx) for static files
7. Enable HTTPS with SSL certificates

The system is now production-ready with proper authentication, cloud storage, and database management! 🎉
