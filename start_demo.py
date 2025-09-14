"""
Start the Catch Meow Demo Server

This starts the MCP server for the simplified demo workflow:
1. Le Chat asks for name and profile info
2. User provides .wav files directly 
3. Server processes files and calculates bluff score
4. Updates GUI with metrics and leaderboard
"""

import subprocess
import sys
import os

def main():
    print("🎯 Starting Catch Meow Demo Server...")
    print("📊 Demo Workflow:")
    print("  1. Use save_profile to set player name")
    print("  2. Use process_demo_audio_files with .wav file paths")
    print("  3. Check results with get_player_metrics_dashboard")
    print()
    
    # Check if mainmcp1.py exists
    if not os.path.exists("mainmcp1.py"):
        print("❌ Error: mainmcp1.py not found!")
        print("Make sure you're in the correct directory.")
        return
    
    try:
        # Start the FastMCP server
        print("🚀 Starting MCP server on port 3000...")
        subprocess.run([sys.executable, "mainmcp1.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()