let mediaRecorder, audioChunks = [], audioBlob;
let recordingTimer, startTime;

const recordBtn = document.getElementById('recordBtn');
const voiceFileInput = document.getElementById('voice_sample');
const enrollForm = document.querySelector('form');
const timer = document.getElementById('timer');

// Audio config for librosa
const audioConfig = { audio: { channelCount: 1, sampleRate: 22050, sampleSize: 16 } };

document.addEventListener('DOMContentLoaded', function() {
    if (!navigator.mediaDevices?.getUserMedia) {
        recordBtn.disabled = true;
        recordBtn.className = 'bg-gray-400 text-white px-6 py-2 rounded-md font-medium cursor-not-allowed mb-4';
        recordBtn.innerHTML = '<i class="fas fa-exclamation-triangle mr-2"></i>Not supported';
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
            document.getElementById('recordingTime').classList.add('hidden');
            
            recordBtn.className = 'bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-md font-medium transition-colors mb-4';
            recordBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Voice Recorded';
        };
        
        mediaRecorder.start();
        startTime = Date.now();
        
        recordBtn.className = 'bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-md font-medium transition-colors mb-4';
        recordBtn.innerHTML = '<i class="fas fa-stop mr-2"></i>Stop Recording';
        document.getElementById('recordingTime').classList.remove('hidden');
        
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
    audioDiv.className = 'mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200';
    audioDiv.innerHTML = `
        <label class="block text-sm font-medium text-gray-700 mb-2">Recorded Audio</label>
        <audio controls class="w-full mb-3 rounded-md"></audio>
        <div class="flex justify-center">
            <button type="button" class="px-4 py-2 border border-blue-300 text-blue-700 rounded-md hover:bg-blue-50 transition-colors" onclick="reRecord()">
                <i class="fas fa-redo mr-2"></i>Re-record
            </button>
        </div>
    `;
    
    audioDiv.querySelector('audio').src = URL.createObjectURL(audioBlob);
    document.getElementById('recordingStatus').appendChild(audioDiv);
}

function reRecord() {
    audioBlob = null;
    voiceFileInput.required = true;
    
    const audioPlayback = document.getElementById('audioPlayback');
    if (audioPlayback) audioPlayback.remove();
    
    recordBtn.className = 'btn-record text-white px-6 py-2 rounded-md font-medium transition-colors mb-4';
    recordBtn.innerHTML = '<i class="fas fa-microphone mr-2"></i>Start Recording';
}

// Convert to WAV
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
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.custom-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Determine colors based on type
    const alertColors = {
        'success': 'bg-green-50 border-green-200 text-green-800',
        'error': 'bg-red-50 border-red-200 text-red-800',
        'warning': 'bg-yellow-50 border-yellow-200 text-yellow-800',
        'info': 'bg-blue-50 border-blue-200 text-blue-800'
    };
    
    const iconMap = {
        'success': 'fa-check-circle text-green-600',
        'error': 'fa-exclamation-circle text-red-600',
        'warning': 'fa-exclamation-triangle text-yellow-600',
        'info': 'fa-info-circle text-blue-600'
    };
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `custom-alert mb-4 p-4 rounded-md border ${alertColors[type] || alertColors['info']} relative transition-all duration-300 ease-in-out`;
    alertDiv.innerHTML = `
        <div class="flex items-center justify-between">
            <div class="flex items-center">
                <i class="fas ${iconMap[type] || iconMap['info']} mr-2"></i>
                <span>${message}</span>
            </div>
            <button type="button" class="text-gray-400 hover:text-gray-600 focus:outline-none" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Insert alert at the top of the card body or form container
    const container = document.querySelector('.p-6') || document.querySelector('.card-body');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }
    
    // Add entrance animation
    alertDiv.style.opacity = '0';
    alertDiv.style.transform = 'translateY(-10px)';
    setTimeout(() => {
        alertDiv.style.opacity = '1';
        alertDiv.style.transform = 'translateY(0)';
    }, 10);
    
    // Auto-hide success alerts
    if (type === 'success') {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.style.opacity = '0';
                alertDiv.style.transform = 'translateY(-10px)';
                setTimeout(() => alertDiv.remove(), 300);
            }
        }, 3000);
    }
}

// Handle form submission
enrollForm.addEventListener('submit', function(e) {
    e.preventDefault(); // Always prevent default
    
    const studentId = document.getElementById('student_id').value.trim();
    const studentName = document.getElementById('student_name').value.trim();
    
    console.log('Form submission - Student ID:', studentId, 'Student Name:', studentName);
    
    if (!studentId || !studentName) {
        showAlert('Please fill in all required fields', 'error');
        return;
    }
    
    if (!audioBlob && !voiceFileInput.files.length) {
        showAlert('Please record your voice or upload an audio file', 'error');
        return;
    }
    
    // Show loading spinner
    showLoading();
    
    const formData = new FormData();
    
    // Explicitly add form fields
    formData.append('student_id', studentId);
    formData.append('student_name', studentName);
    
    // Add teacher_id from hidden field
    const teacherIdField = document.querySelector('input[name="teacher_id"]');
    if (teacherIdField) {
        formData.append('teacher_id', teacherIdField.value);
        console.log('Added teacher_id to form:', teacherIdField.value);
    } else {
        console.error('Teacher ID field not found!');
    }
    
    // Add recorded audio or uploaded file
    if (audioBlob) {
        formData.append('recorded_audio', audioBlob, 'enrollment_recording.wav');
        console.log('Added recorded audio to form');
    } else if (voiceFileInput.files.length > 0) {
        formData.append('voice_sample', voiceFileInput.files[0]);
        console.log('Added uploaded file to form');
    }
    
    // Debug: Log what we're sending
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
            showAlert(data.message || 'Student enrolled successfully!', 'success');
            // Reset form after successful enrollment
            enrollForm.reset();
            audioBlob = null;
            voiceFileInput.required = true;
            
            // Remove audio playback
            const audioPlayback = document.getElementById('audioPlayback');
            if (audioPlayback) audioPlayback.remove();
            
            // Reset record button
            recordBtn.className = 'btn-record text-white px-6 py-2 rounded-md font-medium transition-colors mb-4';
            recordBtn.innerHTML = '<i class="fas fa-microphone mr-2"></i>Start Recording';
        } else {
            showAlert(data.message || 'Enrollment failed');
        }
    })
    .catch(error => {
        hideLoading();
        console.error('Error:', error);
        showAlert('Network error. Please try again.', 'error');
    });
});

function showLoading() {
    const overlay = document.createElement('div');
    overlay.id = 'loadingOverlay';
    overlay.innerHTML = `
        <div class="text-center text-white">
            <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent mb-4"></div>
            <h5 class="text-xl font-semibold mb-2">Enrolling Student...</h5>
            <p class="text-blue-200">Processing voice sample...</p>
            <div class="mt-4">
                <div class="bg-gray-200 rounded-full h-2 w-64 mx-auto">
                    <div class="bg-blue-500 h-2 rounded-full animate-pulse" style="width: 60%"></div>
                </div>
                <p class="text-sm text-gray-300 mt-2">Please wait while we process your enrollment...</p>
            </div>
        </div>
    `;
    overlay.className = `
        fixed inset-0 bg-black bg-opacity-70 flex justify-center items-center z-50 
        backdrop-blur-sm transition-all duration-300 ease-in-out
    `;
    
    // Add entrance animation
    overlay.style.opacity = '0';
    document.body.appendChild(overlay);
    
    // Trigger entrance animation
    setTimeout(() => {
        overlay.style.opacity = '1';
    }, 10);
    
    // Disable form
    enrollForm.querySelectorAll('input, button').forEach(el => el.disabled = true);
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        // Add exit animation
        overlay.style.opacity = '0';
        overlay.style.transform = 'scale(0.95)';
        
        setTimeout(() => {
            overlay.remove();
        }, 300);
    }
    
    // Re-enable form
    enrollForm.querySelectorAll('input, button').forEach(el => el.disabled = false);
}


voiceFileInput.addEventListener('change', function() {
    if (this.files.length > 0) {
        audioBlob = null;
        const audioPlayback = document.getElementById('audioPlayback');
        if (audioPlayback) audioPlayback.remove();
        recordBtn.className = 'btn-record text-white px-6 py-2 rounded-md font-medium transition-colors mb-4';
        recordBtn.innerHTML = '<i class="fas fa-microphone mr-2"></i>Start Recording';
    }
});

// Add CSS for the custom button
const style = document.createElement('style');
style.textContent = `
    .btn-record { 
        background: linear-gradient(45deg, #3b82f6, #1d4ed8);
        border: none;
        transition: all 0.3s ease;
    }
    .btn-record:hover { 
        background: linear-gradient(45deg, #1d4ed8, #1e40af);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    .btn-record:active {
        transform: translateY(0);
    }
`;
document.head.appendChild(style);