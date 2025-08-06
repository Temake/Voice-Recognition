#!/bin/bash
# deploy.sh - Deployment script for production

echo "🚀 Starting Voice Attendance System Deployment..."

# Check Python version
echo "📋 Checking Python version..."
python3 --version

# Create virtual environment
echo "🔧 Setting up virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements-production.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p voice_samples
mkdir -p logs

# Set file permissions
echo "🔐 Setting permissions..."
chmod -R 755 voice_samples
chmod -R 755 logs

# Test the application
echo "🧪 Testing application..."
python3 -c "import main; print('✅ Main module loads successfully')"

# Start the application
echo "🌟 Starting Voice Attendance System..."
echo "🌐 Application will be available at: http://0.0.0.0:5000"
echo "📊 Monitor at: http://0.0.0.0:5000/api/status"

gunicorn main:app --bind 0.0.0.0:5000 --workers 2 --timeout 120 --access-logfile logs/access.log --error-logfile logs/error.log
