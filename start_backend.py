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
    """Install the backend nepse package"""
    backend_path = Path("backend")
    if not backend_path.exists():
        print("❌ Backend folder not found!")
        print("Make sure you're running this from the project root directory.")
        return False
    
    print("📦 Installing backend dependencies...")
    try:
        # Change to backend directory and install
        original_dir = os.getcwd()
        os.chdir(backend_path)
        
        result = subprocess.run([sys.executable, "-m", "pip", "install", "."], 
                              capture_output=True, text=True)
        
        os.chdir(original_dir)
        
        if result.returncode == 0:
            print("✅ Backend installed successfully!")
            return True
        else:
            print(f"❌ Installation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Installation error: {e}")
        return False

def start_server():
    """Start the local backend server"""
    server_path = Path("backend/example/NepseServer.py")
    
    if not server_path.exists():
        print("❌ Server file not found!")
        print("Expected location: backend/example/NepseServer.py")
        return False
    
    print("🚀 Starting local NEPSE backend server...")
    print("📍 Server will run at: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("="*50)
    
    try:
        # Change to server directory and start
        original_dir = os.getcwd()
        os.chdir("backend/example")
        
        # Start the server
        subprocess.run([sys.executable, "NepseServer.py"])
        
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