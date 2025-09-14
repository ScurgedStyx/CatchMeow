"""
Simple Demo Launcher
Opens the HTML file in the default browser for demo purposes
"""

import webbrowser
import os
import sys
from pathlib import Path

def find_html_file():
    """Find the index.html file"""
    current_dir = Path(__file__).parent
    html_file = current_dir / "index.html"
    
    if html_file.exists():
        return html_file
    else:
        print("❌ index.html not found in current directory")
        print(f"Current directory: {current_dir}")
        return None

def main():
    print("🎯 Catch Meow Demo Launcher")
    print("=" * 50)
    
    html_file = find_html_file()
    if not html_file:
        input("Press Enter to exit...")
        return
    
    file_url = f"file://{html_file.absolute()}"
    
    print(f"📊 Opening demo GUI...")
    print(f"🔗 URL: {file_url}")
    print()
    print("💡 Demo Features:")
    print("  • Upload audio files (.wav, .mp3, .m4a)")
    print("  • Simulated voice analysis")
    print("  • Real-time metric updates")
    print("  • Interactive leaderboard")
    print()
    print("🎤 To test:")
    print("  1. Click 'Upload Audio Files' button")
    print("  2. Select 1-5 audio files")
    print("  3. Watch the analysis results!")
    print()
    
    try:
        webbrowser.open(file_url)
        print("✅ Demo opened in your default browser")
    except Exception as e:
        print(f"❌ Failed to open browser: {e}")
        print(f"💡 Manually open: {file_url}")
    
    print("\n⚠️  Note: This is demo mode with simulated results")
    print("   For real analysis, install Python dependencies and use web_server.py")
    print()
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()