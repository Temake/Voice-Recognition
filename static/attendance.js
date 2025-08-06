let mediaRecorder;
let audioChunks = [];
let audioBlob;
let recordingTimer;
let startTime;

const recordBtn = document.getElementById('recordBtn');
const stopBtn = document.getElementById('stopBtn');
const audioPlayback = document.querySelector('#audioPlayback audio');
const voiceFileInput = document.getElementById('voice_sample');
const attendanceForm = document.querySelector('form');
const recordingTime = document.getElementById('recordingTime');
const timer = document.getElementById('timer');

// Audio configuration for librosa
const audioConfig = {
    audio: {
        channelCount: 1,
        sampleRate: 22050,
        sampleSize: 16
    }
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Hide audio playback initially
    document.getElementById('audioPlayback').style.display = 'none';
    
    // Check browser compatibility
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        recordBtn.disabled = true;
        recordBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Browser not supported';
    }
});

recordBtn.addEventListener('click', startRecording);
stopBtn.addEventListener('click', stopRecording);

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia(audioConfig);
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = async () => {
            const webmBlob = new Blob(audioChunks, { type: 'audio/webm' });
            audioBlob = await convertToWav(webmBlob);
            
            // Show audio playback
            audioPlayback.src = URL.createObjectURL(audioBlob);
            document.getElementById('audioPlayback').style.display = 'block';
            
            // Make voice file input optional since we have recording
            voiceFileInput.required = false;
            
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            
            // Clear timer
            clearInterval(recordingTimer);
            recordingTime.style.display = 'none';
        };
        
        // Start recording
        mediaRecorder.start();
        startTime = Date.now();
        
        // Update UI
        recordBtn.style.display = 'none';
        stopBtn.style.display = 'inline-block';
        recordingTime.style.display = 'block';
        
        // Start timer
        recordingTimer = setInterval(updateTimer, 100);
        
    } catch (error) {
        console.error('Recording error:', error);
        showAlert('Error accessing microphone. Please check permissions.', 'danger');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        
        // Update UI
        recordBtn.style.display = 'inline-block';
        stopBtn.style.display = 'none';
    }
}

function updateTimer() {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    timer.textContent = elapsed;
}

// Convert WebM to WAV format
async function convertToWav(webmBlob) {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: 22050
    });
    
    return new Promise((resolve) => {
        const fileReader = new FileReader();
        fileReader.onload = async function(e) {
            try {
                const audioBuffer = await audioContext.decodeAudioData(e.target.result);
                const wavBlob = audioBufferToWav(audioBuffer);
                resolve(wavBlob);
            } catch (error) {
                console.error('Conversion error:', error);
                resolve(webmBlob);
            }
        };
        fileReader.readAsArrayBuffer(webmBlob);
    });
}

function audioBufferToWav(audioBuffer) {
    const sampleRate = 22050;
    const numberOfChannels = 1;
    
    // Convert to mono
    let audioData;
    if (audioBuffer.numberOfChannels === 1) {
        audioData = audioBuffer.getChannelData(0);
    } else {
        const left = audioBuffer.getChannelData(0);
        const right = audioBuffer.getChannelData(1);
        audioData = new Float32Array(left.length);
        for (let i = 0; i < left.length; i++) {
            audioData[i] = (left[i] + right[i]) / 2;
        }
    }
    
    const length = audioData.length;
    const arrayBuffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(arrayBuffer);
    
    // WAV header
    const writeString = (offset, string) => {
        for (let i = 0; i < string.length; i++) {
            view.setUint8(offset + i, string.charCodeAt(i));
        }
    };
    
    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, numberOfChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(36, 'data');
    view.setUint32(40, length * 2, true);
    
    // Convert to 16-bit PCM
    for (let i = 0; i < length; i++) {
        const sample = Math.max(-1, Math.min(1, audioData[i]));
        view.setInt16(44 + i * 2, sample * 0x7FFF, true);
    }
    
    return new Blob([arrayBuffer], { type: 'audio/wav' });
}

// Handle form submission with loading spinner
attendanceForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Validate student selection
    const studentSelect = document.getElementById('student_id');
    if (!studentSelect.value) {
        showAlert('Please select a student', 'warning');
        return;
    }
    
    // Check if we have audio (either recorded or uploaded)
    if (!audioBlob && !voiceFileInput.files.length) {
        showAlert('Please record your voice or upload an audio file', 'warning');
        return;
    }
    
    // Show loading spinner
    showLoadingSpinner();
    
    const formData = new FormData(this);
    
    // Add recorded audio if available
    if (audioBlob) {
        formData.append('recorded_audio', audioBlob, 'attendance_recording.wav');
    }
    
    // Submit form
    fetch(this.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoadingSpinner();
        
        if (data.success) {
            showAlert('Attendance marked successfully!', 'success');
            // Reset form
            resetForm();
        } else {
            showAlert(data.message || 'Attendance marking failed', 'danger');
        }
    })
    .catch(error => {
        hideLoadingSpinner();
        console.error('Upload error:', error);
        showAlert('Network error. Please try again.', 'danger');
    });
});

// Reset form function
function resetForm() {
    attendanceForm.reset();
    audioBlob = null;
    document.getElementById('audioPlayback').style.display = 'none';
    audioPlayback.src = '';
    voiceFileInput.required = true;
    recordBtn.style.display = 'inline-block';
    stopBtn.style.display = 'none';
    recordingTime.style.display = 'none';
}

// Loading spinner functions
function showLoadingSpinner() {
    // Create loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'loadingOverlay';
    loadingOverlay.innerHTML = `
        <div class="loading-content">
            <div class="spinner-border text-success" role="status" style="width: 3rem; height: 3rem;">
                <span class="visually-hidden">Loading...</span>
            </div>
            <h5 class="mt-3">Processing Attendance...</h5>
            <p class="text-muted">Verifying voice sample, please wait.</p>
        </div>
    `;
    
    // Add styles
    loadingOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        color: white;
        text-align: center;
    `;
    
    document.body.appendChild(loadingOverlay);
    
    // Disable form elements
    const formElements = attendanceForm.querySelectorAll('input, select, button');
    formElements.forEach(element => {
        element.disabled = true;
    });
}

function hideLoadingSpinner() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
    
    // Re-enable form elements
    const formElements = attendanceForm.querySelectorAll('input, select, button');
    formElements.forEach(element => {
        element.disabled = false;
    });
}

// Alert function
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert alert at the top of the card body
    const cardBody = document.querySelector('.card-body');
    cardBody.insertBefore(alertDiv, cardBody.firstChild);
    
    // Auto-hide success alerts
    if (type === 'success') {
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
}

// File input change handler
voiceFileInput.addEventListener('change', function() {
    if (this.files.length > 0) {
        // If file is selected, make recording optional
        audioBlob = null;
        document.getElementById('audioPlayback').style.display = 'none';
    }
});