"""
Audio Feature Extraction Module
Extracts speech features from .wav files using librosa
"""

import librosa
import numpy as np
import os
from typing import Dict, Optional

def extract_features_from_wav(file_path: str, sr: int = 16000) -> Dict[str, float]:
    """
    Extract comprehensive speech features from a .wav file
    
    Args:
        file_path: Path to the .wav file
        sr: Sample rate for loading audio
        
    Returns:
        Dictionary containing extracted features
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    try:
        # Load audio file
        y, actual_sr = librosa.load(file_path, sr=sr, mono=True)
        total_duration = len(y) / actual_sr
        
        # Split into speech and non-speech segments
        intervals = librosa.effects.split(y, top_db=20)  # More sensitive silence detection
        
        if len(intervals) > 0:
            speech_samples = sum(end - start for start, end in intervals)
            speech_duration = speech_samples / actual_sr
            pause_count = max(0, len(intervals) - 1)
        else:
            speech_duration = 0.0
            pause_count = 0
        
        # Calculate pause metrics
        pause_duration = max(0.0, total_duration - speech_duration)
        pause_ratio = pause_duration / max(speech_duration, 1e-6)
        
        # Extract speech segments for analysis
        if len(intervals) > 0:
            speech_segments = [y[start:end] for start, end in intervals]
            speech_audio = np.concatenate(speech_segments)
        else:
            speech_audio = np.array([])
        
        # Initialize features with defaults
        features = {
            "duration_s": round(total_duration, 3),
            "speech_dur_s": round(speech_duration, 3),
            "pause_ratio": round(pause_ratio, 4),
            "pause_count": int(pause_count),
            "mean_f0": 0.0,
            "mean_rms_db": -120.0,
            "max_rms_db": -120.0,
        }
        
        # Only analyze if we have sufficient speech audio
        if len(speech_audio) > actual_sr * 0.1:  # At least 0.1 seconds of speech
            
            # Calculate F0 (fundamental frequency)
            try:
                f0, voiced_flag, _ = librosa.pyin(
                    speech_audio, 
                    fmin=75, 
                    fmax=400, 
                    sr=actual_sr,
                    frame_length=2048,
                    hop_length=512
                )
                voiced_f0 = f0[voiced_flag] if voiced_flag is not None else f0[~np.isnan(f0)]
                if len(voiced_f0) > 0:
                    features["mean_f0"] = round(float(np.mean(voiced_f0)), 2)
            except Exception as e:
                print(f"Warning: F0 extraction failed: {e}")
            
            # Calculate RMS energy features
            try:
                rms = librosa.feature.rms(
                    y=speech_audio, 
                    frame_length=2048, 
                    hop_length=512
                )[0]
                
                # Convert to dB scale
                rms_db = 20 * np.log10(np.maximum(rms, 1e-8))
                
                if len(rms_db) > 0:
                    features["mean_rms_db"] = round(float(np.mean(rms_db)), 2)
                    features["max_rms_db"] = round(float(np.max(rms_db)), 2)
                    
            except Exception as e:
                print(f"Warning: RMS extraction failed: {e}")
        
        return features
        
    except Exception as e:
        raise RuntimeError(f"Failed to extract features from {file_path}: {str(e)}")

def batch_extract_features(file_paths: list, sr: int = 16000) -> Dict[str, Dict[str, float]]:
    """
    Extract features from multiple .wav files
    
    Args:
        file_paths: List of paths to .wav files
        sr: Sample rate for loading audio
        
    Returns:
        Dictionary mapping file paths to their extracted features
    """
    results = {}
    
    for file_path in file_paths:
        try:
            features = extract_features_from_wav(file_path, sr)
            results[file_path] = features
            print(f"✅ Extracted features from: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"❌ Failed to extract features from {file_path}: {e}")
            results[file_path] = None
    
    return results

if __name__ == "__main__":
    # Test the feature extraction
    test_files = ["test1.wav", "test2.wav", "test3.wav"]  # Replace with actual file paths
    
    for file_path in test_files:
        if os.path.exists(file_path):
            try:
                features = extract_features_from_wav(file_path)
                print(f"\nFeatures for {file_path}:")
                for key, value in features.items():
                    print(f"  {key}: {value}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        else:
            print(f"File not found: {file_path}")