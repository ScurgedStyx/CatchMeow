"""
Installation Script for Catch Meow Voice Analysis
Helps set up the Python environment and dependencies
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python():
    """Check if Python is available"""
    try:
        version = sys.version_info
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("⚠️  Warning: Python 3.8+ recommended for best compatibility")
        return True
    except Exception as e:
        print(f"❌ Python check failed: {e}")
        return False

def install_package(package):
    """Install a single package"""
    try:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def check_package(package):
    """Check if a package is already installed"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    print("🎯 Catch Meow Voice Analysis - Installation")
    print("=" * 50)
    
    if not check_python():
        print("❌ Python installation issues detected")
        input("Press Enter to exit...")
        return
    
    # Required packages
    packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS', 
        'librosa': 'librosa',
        'numpy': 'numpy'
    }
    
    print("\n📋 Checking required packages...")
    
    # Check which packages need installation
    to_install = []
    for import_name, pip_name in packages.items():
        if check_package(import_name):
            print(f"✅ {pip_name} already installed")
        else:
            print(f"❌ {pip_name} not found - will install")
            to_install.append(pip_name)
    
    if not to_install:
        print("\n🎉 All packages already installed!")
        print("\nYou can now run:")
        print("  • python demo_launcher.py (for demo mode)")
        print("  • python web_server.py (for full analysis)")
        input("\nPress Enter to exit...")
        return
    
    print(f"\n🔧 Need to install {len(to_install)} packages:")
    for pkg in to_install:
        print(f"  • {pkg}")
    
    response = input("\nProceed with installation? (y/n): ").lower().strip()
    if response != 'y' and response != 'yes':
        print("❌ Installation cancelled")
        input("Press Enter to exit...")
        return
    
    print("\n🚀 Starting installation...")
    
    # Install packages
    failed = []
    for pip_name in to_install:
        if not install_package(pip_name):
            failed.append(pip_name)
    
    print("\n" + "=" * 50)
    
    if failed:
        print(f"❌ Installation completed with {len(failed)} errors:")
        for pkg in failed:
            print(f"  • {pkg}")
        print("\n💡 Try installing failed packages manually:")
        for pkg in failed:
            print(f"  pip install {pkg}")
    else:
        print("🎉 All packages installed successfully!")
        print("\n🎯 Next steps:")
        print("  1. Run: python demo_launcher.py (demo mode)")
        print("  2. Or run: python web_server.py (full analysis)")
        print("  3. Open browser and upload audio files!")
        print("\n📖 See README.md for detailed usage guide")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()