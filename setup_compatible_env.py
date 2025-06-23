#!/usr/bin/env python3
"""
Setup script to ensure compatible versions for optimal diarization quality.
Run this script to fix version compatibility issues using uv.
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("🔧 Setting up compatible environment for optimal diarization quality...")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("transcribe_advanced.py").exists():
        print("❌ Please run this script from the project directory.")
        sys.exit(1)
    
    print("This script will:")
    print("1. Check current package versions")
    print("2. Use uv sync to install compatible versions")
    print("3. Create a backup of your current versions")
    print()
    
    confirm = input("Proceed with setup? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Step 1: Create backup
    print("\n📦 Creating backup of current versions...")
    try:
        result = subprocess.run([sys.executable, "fix_compatibility.py", "check"], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not create backup: {e}")
    
    # Step 2: Sync dependencies with uv
    print("\n🔄 Syncing dependencies with uv...")
    try:
        result = subprocess.run(["uv", "sync"], check=True, capture_output=True, text=True)
        print("✅ Dependencies synced successfully!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to sync dependencies: {e}")
        print("Error output:", e.stderr)
        return
    
    # Step 3: Verify installation
    print("\n🔍 Verifying installation...")
    try:
        result = subprocess.run([sys.executable, "fix_compatibility.py", "check"], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Could not verify installation: {e}")
    
    print("\n✅ Setup completed successfully!")
    print("\nNext steps:")
    print("1. Restart your Python environment")
    print("2. Run your transcription script with: uv run transcribe_advanced.py")
    print("3. If you need to restore original versions: python fix_compatibility.py restore")

if __name__ == "__main__":
    main() 