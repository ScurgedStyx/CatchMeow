"""
Flask Backend for Audio Analysis
Connects the Python audio processing to the web GUI
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import tempfile
import json
from werkzeug.utils import secure_filename
from audio_pipeline import AudioAnalyzer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize audio analyzer
audio_analyzer = AudioAnalyzer()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Serve the main GUI"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files (CSS, JS, images)"""
    return send_from_directory('.', filename)

@app.route('/analyze_audio', methods=['POST'])
def analyze_audio():
    """Handle audio file uploads and analysis"""
    try:
        logger.info("Received audio analysis request")
        
        # Check if files were uploaded
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'success': False, 'error': 'No files selected'}), 400
        
        # Filter and save valid files
        saved_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                timestamp = str(int(time.time()))
                filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                saved_files.append(filepath)
                logger.info(f"Saved file: {filepath}")
        
        if not saved_files:
            return jsonify({'success': False, 'error': 'No valid audio files uploaded'}), 400
        
        logger.info(f"Processing {len(saved_files)} files")
        
        # Analyze the audio files
        results = audio_analyzer.analyze_for_gui(saved_files)
        
        # Clean up uploaded files
        for filepath in saved_files:
            try:
                os.remove(filepath)
            except Exception as e:
                logger.warning(f"Failed to delete {filepath}: {e}")
        
        logger.info(f"Analysis complete. Score: {results.get('bluff_score', 'N/A')}")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Audio analysis error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analyze_demo', methods=['POST'])
def analyze_demo():
    """Demo endpoint that generates fake results without file upload"""
    try:
        data = request.json or {}
        num_files = data.get('num_files', 1)
        
        # Generate demo results
        if num_files >= 5:
            # Full session simulation
            results = generate_demo_session_results()
        else:
            # Single file simulation
            results = generate_demo_single_results()
        
        logger.info(f"Generated demo results. Score: {results['bluff_score']}")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Demo analysis error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_demo_session_results():
    """Generate realistic demo results for full session"""
    import random
    
    base_score = 20 + random.random() * 60  # 20-80 range
    confidence = 0.7 + random.random() * 0.25  # 0.7-0.95 range
    
    reasons = [
        "Pause patterns differ from conversational baseline",
        "Pitch variation exceeds reading baseline", 
        "Energy levels show stress indicators",
        "Speech rhythm changes detected",
        "Voice tremor detected in target recording",
        "Hesitation markers above baseline threshold"
    ]
    
    selected_reasons = random.sample(reasons, 2 + random.randint(0, 2))
    
    return {
        'success': True,
        'bluff_score': round(base_score, 1),
        'confidence': round(confidence, 2),
        'reasons': selected_reasons,
        'metrics': {
            'pause_ratio': round((0.05 + random.random() * 0.3), 1),  # 0.05-0.35
            'pause_count': random.randint(3, 23),
            'mean_f0': round(120 + random.random() * 80),  # 120-200 Hz
            'mean_energy': round(30 + random.random() * 50),  # 30-80%
            'max_energy': round(50 + random.random() * 40)   # 50-90%
        },
        'analysis_type': 'full_session_baseline',
        'files_analyzed': 5
    }

def generate_demo_single_results():
    """Generate realistic demo results for single file"""
    import random
    
    base_score = 10 + random.random() * 70  # 10-80 range
    confidence = 0.6 + random.random() * 0.2  # 0.6-0.8 range
    
    reasons = [
        "High pause ratio detected",
        "Frequent pausing detected", 
        "Unusual pitch patterns",
        "Energy levels indicate stress",
        "Speech patterns appear normal"
    ]
    
    selected_reasons = random.sample(reasons, 1 + random.randint(0, 2))
    
    return {
        'success': True,
        'bluff_score': round(base_score, 1),
        'confidence': round(confidence, 2),
        'reasons': selected_reasons,
        'metrics': {
            'pause_ratio': round((0.02 + random.random() * 0.25), 1),
            'pause_count': random.randint(1, 15),
            'mean_f0': round(100 + random.random() * 100),
            'mean_energy': round(20 + random.random() * 60),
            'max_energy': round(40 + random.random() * 50)
        },
        'analysis_type': 'single_file_simple',
        'files_analyzed': 1
    }

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'analyzer_ready': True})

if __name__ == '__main__':
    import time
    
    print("🎯 Starting Catch Meow Audio Analysis Server...")
    print("📊 GUI will be available at: http://localhost:5000")
    print("🎤 Upload .wav files to analyze voice patterns")
    print("💡 Press Ctrl+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)