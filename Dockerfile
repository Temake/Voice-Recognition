# Use stable Python version with good scientific package support
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (including ffmpeg for audio processing)
RUN apt-get update && apt-get install -y \
    libpq-dev python3-dev \
    build-essential \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements-production.txt requirements.txt

# Upgrade pip and install dependencies with prebuilt wheels where possible
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary folders
RUN mkdir -p voice_samples uploads data

# Expose port
EXPOSE 5000

# Set environment variables for Flask
ENV FLASK_ENV=production
ENV PORT=5000

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Start the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
