# Catch Meow Voice Analysis - Quick Start Guide

## 🎯 What This System Does

This system analyzes voice recordings to detect potential bluffs using advanced audio feature extraction and baseline comparison algorithms. It integrates with the Catch Meow game interface to provide real-time voice analysis results.

## 📁 File Overview

### Core Audio Analysis Files
- **`audio_extractor.py`** - Extracts comprehensive speech features from audio files using librosa
- **`bluff_calculator.py`** - Implements advanced baseline comparison algorithm for bluff detection  
- **`audio_pipeline.py`** - Combines extraction and calculation into unified analysis pipeline
- **`web_server.py`** - Flask backend server for file uploads and analysis

### Frontend Integration Files
- **`script.js`** - Enhanced JavaScript with audio analysis integration and file upload UI
- **`styles.css`** - Additional styling for modal dialogs, progress indicators, and upload buttons
- **`index.html`** - Main GUI interface (assumed to exist in your project)

### Utilities
- **`demo_launcher.py`** - Simple launcher to open GUI demo without backend dependencies
- **`README.md`** - This guide

## 🚀 How to Run

### Option 1: Demo Mode (No Dependencies Required)
```bash
python demo_launcher.py
```
- Opens the GUI in your browser
- Uses simulated analysis results
- Perfect for testing the interface

### Option 2: Full Analysis Mode (Requires Dependencies)
1. Install Python dependencies:
   ```bash
   pip install flask flask-cors librosa numpy
   ```

2. Start the Flask backend:
   ```bash
   python web_server.py
   ```

3. Open browser to: `http://localhost:5000`

4. Upload .wav audio files and get real analysis results!

## 🎤 How to Use the Voice Analysis

1. **Upload Audio Files**: Click the "Upload Audio Files" button and select 1-5 audio files
2. **Watch Analysis**: The system will analyze each file and show progress
3. **View Results**: Results appear in a modal with detailed metrics:
   - **Bluff Score**: 0-100% likelihood of bluffing
   - **Confidence**: How confident the algorithm is
   - **Key Metrics**: Pause patterns, pitch variations, energy levels

## 📊 Advanced Algorithm Features

The system uses a sophisticated baseline comparison method:
- **Conversational vs Reading Baselines**: Compares speech patterns against natural vs scripted speech
- **Robust Statistics**: Uses MAD (Median Absolute Deviation) for outlier-resistant analysis
- **Weighted Feature Contributions**: Combines multiple voice characteristics intelligently
- **Session Management**: Tracks multiple recordings for improved accuracy

## 🔧 Technical Details

### Supported Audio Formats
- WAV files (recommended)
- MP3 files 
- M4A files

### Voice Features Analyzed
- **Pause Detection**: Frequency and duration of speech pauses
- **Fundamental Frequency (F0)**: Pitch variations and patterns
- **RMS Energy**: Volume and energy level changes
- **Spectral Features**: Voice quality characteristics

### Performance
- Processes typical 30-second audio clips in 1-3 seconds
- Handles batch uploads of up to 5 files
- Automatic cleanup of uploaded files

## 🎮 Integration with Catch Meow Game

The voice analysis integrates seamlessly with your existing game:
- Results update the main leaderboard
- Scores are color-coded (green = likely truthful, red = likely bluffing)
- Modal displays show detailed analysis breakdowns
- Progress indicators keep players engaged during analysis

## 🐛 Troubleshooting

### Demo Mode Issues
- If demo_launcher.py doesn't open browser, manually copy the file:// URL
- Make sure index.html exists in the same directory

### Full Mode Issues
- **Import errors**: Install dependencies with `pip install flask flask-cors librosa numpy`
- **Port conflicts**: If port 5000 is busy, the server will try 5001, 5002, etc.
- **File upload fails**: Check file format (WAV recommended) and size (<10MB)
- **Analysis errors**: Verify audio files have clear speech content

### Audio Quality Tips
- Use WAV files for best results
- Ensure clear speech with minimal background noise
- 15-60 second clips work best
- Single speaker recordings preferred

## 🎯 Next Steps

1. Test with demo mode first to verify GUI works
2. Install dependencies and try full analysis mode
3. Upload some sample audio files to test the algorithm
4. Integrate with your complete Catch Meow game logic
5. Customize the UI styling to match your game theme

## 📝 Notes

- The demo mode shows realistic but simulated results
- Real analysis requires audio processing dependencies
- The algorithm improves with more baseline data
- Consider adding user feedback to refine scoring

Happy analyzing! 🎤✨
