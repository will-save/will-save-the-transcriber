#!/usr/bin/env python3
"""
Setup script to ensure compatible versions for optimal diarization quality.
Run this script to fix version compatibility issues.
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
    print("2. Install compatible versions for optimal diarization quality")
    print("3. Create a backup of your current versions")
    print()
    
    confirm = input("Proceed with setup? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Run the compatibility fix script
    try:
        result = subprocess.run([sys.executable, "fix_compatibility.py"], check=True)
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Restart your Python environment")
        print("2. Run your transcription script")
        print("3. If you need to restore original versions: python fix_compatibility.py restore")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Setup failed: {e}")
        print("You can try running the fix manually:")
        print("   python fix_compatibility.py")

if __name__ == "__main__":
    main() 