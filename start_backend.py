#!/usr/bin/env python3
"""
Simple script to start the local NEPSE backend server
"""
import os
import sys
import subprocess
from pathlib import Path

def check_backend_installed():
    """Check if nepse package is installed"""
    try:
        import nepse
        return True
    except ImportError:
        return False

def install_backend():
    """Install the backend dependencies"""
    backend_path = Path("backend")
    if not backend_path.exists():
        print("❌ Backend folder not found!")
        print("Make sure you're running this from the project root directory.")
        return False
    
    print("📦 Installing backend dependencies...")
    try:
        # Install backend requirements first
        original_dir = os.getcwd()
        os.chdir(backend_path)
        
        # Install requirements from backend/requirements.txt
        print("📦 Installing from backend/requirements.txt...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Requirements installation failed: {result.stderr}")
            os.chdir(original_dir)
            return False
        
        # Also install the backend package itself if pyproject.toml exists
        if Path("pyproject.toml").exists():
            print("📦 Installing backend package...")
            result2 = subprocess.run([sys.executable, "-m", "pip", "install", "."], 
                                  capture_output=True, text=True)
            if result2.returncode != 0:
                print(f"⚠️  Backend package installation warning: {result2.stderr}")
                # Don't fail here as the requirements might be enough
        
        os.chdir(original_dir)
        print("✅ Backend dependencies installed successfully!")
        return True
            
    except Exception as e:
        print(f"❌ Installation error: {e}")
        if 'original_dir' in locals():
            os.chdir(original_dir)
        return False

def start_server():
    """Start the local backend server"""
    server_path = Path("backend/server.py")
    
    if not server_path.exists():
        print("❌ Server file not found!")
        print("Expected location: backend/server.py")
        return False
    
    print("🚀 Starting local NEPSE backend server...")
    print("📍 Server will run at: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("="*50)
    
    try:
        # Change to backend directory and start server
        original_dir = os.getcwd()
        os.chdir("backend")
        
        # Start the server using uvicorn (same as the server.py does)
        subprocess.run([sys.executable, "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
        
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
    finally:
        os.chdir(original_dir)

def main():
    print("="*50)
    print("🏠 NEPSE Local Backend Server Starter")
    print("="*50)
    
    # Check if backend is installed
    if not check_backend_installed():
        print("📦 Backend not installed. Installing now...")
        if not install_backend():
            print("\n❌ Failed to install backend. Please install manually:")
            print("   cd backend")
            print("   pip install .")
            return
    else:
        print("✅ Backend already installed")
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()