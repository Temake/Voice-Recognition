let mediaRecorder, audioChunks = [], audioBlob;
let recordingTimer, startTime;

const recordBtn = document.getElementById('recordBtn');
const voiceFileInput = document.getElementById('voice_sample');
const attendanceForm = document.querySelector('form');
const timer = document.getElementById('timer');

// Audio config for librosa compatibility
const audioConfig = { audio: { channelCount: 1, sampleRate: 22050, sampleSize: 16 } };

document.addEventListener('DOMContentLoaded', function() {
    if (!navigator.mediaDevices?.getUserMedia) {
        recordBtn.disabled = true;
        recordBtn.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Not supported';
    }
});

recordBtn.addEventListener('click', toggleRecording);

async function toggleRecording() {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        startRecording();
    } else {
        stopRecording();
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia(audioConfig);
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
        mediaRecorder.onstop = async () => {
            const webmBlob = new Blob(audioChunks, { type: 'audio/webm' });
            audioBlob = await convertToWav(webmBlob);
            
            showAudioPlayback();
            voiceFileInput.required = false;
            stream.getTracks().forEach(track => track.stop());
            clearInterval(recordingTimer);
            document.getElementById('recordingTime').style.display = 'none';
            
            recordBtn.className = 'btn btn-success mb-3';
            recordBtn.innerHTML = '<i class="fas fa-check me-2"></i>Voice Recorded';
        };
        
        mediaRecorder.start();
        startTime = Date.now();
        
        recordBtn.className = 'btn btn-danger mb-3';
        recordBtn.innerHTML = '<i class="fas fa-stop me-2"></i>Stop Recording';
        document.getElementById('recordingTime').style.display = 'block';
        
        recordingTimer = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            timer.textContent = elapsed;
            if (elapsed >= 30) stopRecording(); // Auto-stop at 30s
        }, 1000);
        
    } catch (error) {
        alert('Error accessing microphone. Please check permissions.');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
    }
}

function showAudioPlayback() {
    const existing = document.getElementById('audioPlayback');
    if (existing) existing.remove();
    
    const audioDiv = document.createElement('div');
    audioDiv.id = 'audioPlayback';
    audioDiv.className = 'mt-3';
    audioDiv.innerHTML = `
        <label class="form-label">Recorded Audio</label>
        <audio controls style="width: 100%;"></audio>
        <div class="mt-2">
            <button type="button" class="btn btn-sm btn-outline-primary" onclick="reRecord()">
                <i class="fas fa-redo me-1"></i>Re-record
            </button>
        </div>
    `;
    
    audioDiv.querySelector('audio').src = URL.createObjectURL(audioBlob);
    document.getElementById('recordingStatus').appendChild(audioDiv);
    
    // Insert after the recording section
}

function reRecord() {
    audioBlob = null;
    voiceFileInput.required = true;
    
    const audioPlayback = document.getElementById('audioPlayback');
    if (audioPlayback) audioPlayback.remove();
    
    recordBtn.className = 'btn btn-record text-white mb-3';
    recordBtn.innerHTML = '<i class="fas fa-microphone me-2"></i>Start Recording';
}

// Convert to WAV format (same as enroll.js)
async function convertToWav(webmBlob) {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 22050 });
    
    return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = async function(e) {
            try {
                const audioBuffer = await audioContext.decodeAudioData(e.target.result);
                resolve(audioBufferToWav(audioBuffer));
            } catch (error) {
                resolve(webmBlob);
            }
        };
        reader.readAsArrayBuffer(webmBlob);
    });
}

function audioBufferToWav(audioBuffer) {
    const sampleRate = 22050;
    let audioData = audioBuffer.getChannelData(0);
    
    // Mix to mono if stereo
    if (audioBuffer.numberOfChannels > 1) {
        const left = audioBuffer.getChannelData(0);
        const right = audioBuffer.getChannelData(1);
        audioData = new Float32Array(left.length);
        for (let i = 0; i < left.length; i++) {
            audioData[i] = (left[i] + right[i]) / 2;
        }
    }
    
    const length = audioData.length;
    const buffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(buffer);
    
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
    view.setUint16(22, 1, true);
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
    
    return new Blob([buffer], { type: 'audio/wav' });
}

// Handle form submission with proper FormData and spinner
attendanceForm.addEventListener('submit', function(e) {
    e.preventDefault(); // Always prevent default
    
    const studentSelect = document.getElementById('student_id');
    console.log('Student select element:', studentSelect);
    console.log('Student select value:', studentSelect?.value);
    
    if (!studentSelect.value) {
        showAlert('Please select a student', 'warning');
        return;
    }
    
    if (!audioBlob && !voiceFileInput.files.length) {
        showAlert('Please record your voice or upload an audio file', 'warning');
        return;
    }
    
    // Show loading spinner
    showLoading();
    
    const formData = new FormData();
    
    // Explicitly add form fields
    formData.append('student_id', studentSelect.value);
    
    // Add recorded audio or uploaded file
    if (audioBlob) {
        formData.append('recorded_audio', audioBlob, 'attendance_recording.wav');
        console.log('Added recorded audio to form');
    } else if (voiceFileInput.files.length > 0) {
        formData.append('voice_sample', voiceFileInput.files[0]);
        console.log('Added uploaded file to form');
    }
    
    // Debug: Log what we're sending
    console.log('FormData contents:');
    for (let pair of formData.entries()) {
        console.log('FormData:', pair[0], pair[1]);
    }
    
    // Submit via fetch
    fetch(this.action, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showAlert(data.message || 'Attendance marked successfully!', 'success');
            // Reset form after successful attendance
            resetForm();
        } else {
            showAlert(data.message || 'Attendance marking failed', 'danger');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showAlert('Network error. Please try again.', 'danger');
    });
});

function resetForm() {
    attendanceForm.reset();
    audioBlob = null;
    voiceFileInput.required = true;
    
    // Remove audio playback
    const audioPlayback = document.getElementById('audioPlayback');
    if (audioPlayback) audioPlayback.remove();
    
    // Reset record button
    recordBtn.className = 'btn btn-record text-white mb-3';
    recordBtn.innerHTML = '<i class="fas fa-microphone me-2"></i>Start Recording';
}

function showLoading() {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = `
        <div style="text-align: center; color: white;">
            <div class="spinner-border text-success" style="width: 3rem; height: 3rem;"></div>
            <h5 class="mt-3">Processing Attendance...</h5>
            <p>Verifying voice sample, please wait...</p>
        </div>
    `;
    overlay.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.7); display: flex; justify-content: center;
        align-items: center; z-index: 9999;
    `;
    document.body.appendChild(overlay);
    
    // Disable form
    attendanceForm.querySelectorAll('input, select, button').forEach(el => el.disabled = true);
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.remove();
    }
    
    // Re-enable form
    attendanceForm.querySelectorAll('input, select, button').forEach(el => el.disabled = false);
}

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

// Handle file input change
voiceFileInput.addEventListener('change', function() {
    if (this.files.length > 0) {
        audioBlob = null;
        const audioPlayback = document.getElementById('audioPlayback');
        if (audioPlayback) audioPlayback.remove();
        recordBtn.className = 'btn btn-record text-white mb-3';
        recordBtn.innerHTML = '<i class="fas fa-microphone me-2"></i>Start Recording';
    }
});

// Add CSS
const style = document.createElement('style');
style.textContent = `
    .btn-record { background-color: #007bff; border-color: #007bff; }
    .btn-record:hover { background-color: #0056b3; border-color: #0056b3; }
`;
document.head.appendChild(style);