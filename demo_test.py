"""
Demo test script for Catch Meow
Tests the simplified workflow with fake audio data
"""
import os
import numpy as np
import soundfile as sf

def create_demo_wav_files():
    """Create some demo .wav files for testing"""
    
    # Create a simple audio signal (sine wave)
    duration = 3  # seconds
    sample_rate = 16000
    frequency = 440  # Hz (A note)
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    
    # Create 3 different demo files
    for i in range(3):
        # Create slightly different audio for each file
        # Add some pauses and variations to simulate speech patterns
        audio = np.sin(2 * np.pi * (frequency + i*10) * t)
        
        # Add some random pauses (silence)
        for pause_start in np.random.choice(len(audio), size=2, replace=False):
            pause_length = int(0.2 * sample_rate)  # 200ms pause
            end_idx = min(pause_start + pause_length, len(audio))
            audio[pause_start:end_idx] = 0
        
        # Add some noise to make it more realistic
        audio += 0.1 * np.random.normal(0, 1, len(audio))
        
        # Save the file
        filename = f"demo_audio_{i+1}.wav"
        sf.write(filename, audio, sample_rate)
        print(f"Created {filename}")
    
    return ["demo_audio_1.wav", "demo_audio_2.wav", "demo_audio_3.wav"]

if __name__ == "__main__":
    print("Creating demo audio files...")
    files = create_demo_wav_files()
    print(f"Demo files created: {files}")
    print("\nNow you can test with these files using the MCP server!")
    print("Example: process_demo_audio_files('TestPlayer', 'demo_audio_1.wav,demo_audio_2.wav,demo_audio_3.wav')")