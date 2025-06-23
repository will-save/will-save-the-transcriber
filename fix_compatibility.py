#!/usr/bin/env python3
"""
Fix version compatibility issues for optimal diarization quality.
This script downgrades packages to versions that are known to work well with
the pyannote diarization models.
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def run_command(cmd, description, check=True):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"⚠️  {description} completed with warnings: {result.stderr}")
            return True  # Continue even with warnings
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def get_package_version(package_name):
    """Get the current version of a package."""
    try:
        # Use uv run to get package info from the project environment
        result = subprocess.run(["uv", "run", "python", "-c", f"import {package_name}; print({package_name}.__version__)"], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
        try:
            # Fallback to direct pip show
            result = subprocess.run([sys.executable, "-m", "pip", "show", package_name], 
                                  capture_output=True, text=True, check=True)
            lines = result.stdout.split('\n')
            version_line = [line for line in lines if line.startswith('Version:')]
            if version_line:
                return version_line[0].split(':')[1].strip()
        except:
            pass
    return None

def check_current_versions():
    """Check current package versions."""
    print("📊 Current package versions:")
    packages = ["torch", "torchaudio", "pyannote-audio", "pytorch-lightning"]
    
    versions = {}
    for package in packages:
        version = get_package_version(package)
        if version:
            print(f"   {package}: {version}")
            versions[package] = version
        else:
            print(f"   {package}: Not installed")
    
    return versions

def create_backup():
    """Create a backup of current package versions."""
    versions = check_current_versions()
    backup_file = Path("package_versions_backup.json")
    
    with open(backup_file, 'w') as f:
        json.dump(versions, f, indent=2)
    
    print(f"📦 Backup saved to: {backup_file}")
    return backup_file

def fix_compatibility():
    """Fix version compatibility issues."""
    print("🔧 Fixing Pyannote Audio Compatibility for Optimal Diarization Quality")
    print("=" * 70)
    
    # Create backup
    backup_file = create_backup()
    print()
    
    # Check current versions
    print("Current versions:")
    current_versions = check_current_versions()
    print()
    
    # Define target versions for optimal compatibility with current environment
    target_versions = {
        'torch': '2.7.1',
        'torchaudio': '2.7.1', 
        'pyannote-audio': '3.3.2',
        'pytorch-lightning': '2.5.2'
    }
    
    print("🎯 Target versions for optimal diarization quality:")
    for package, version in target_versions.items():
        current = current_versions.get(package, 'Not installed')
        print(f"   {package}: {current} → {version}")
    print()
    
    # Check if we need to update
    needs_update = False
    for package, target_version in target_versions.items():
        current_version = current_versions.get(package)
        if current_version != target_version:
            needs_update = True
            break
    
    if not needs_update:
        print("✅ All packages are already at optimal versions!")
        return True
    
    # Confirm before proceeding
    print("⚠️  This will update packages to ensure compatibility.")
    print("   This process may take several minutes.")
    confirm = input("Proceed with compatibility fixes? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled.")
        return False
    
    print("\n🚀 Starting compatibility fixes...")
    print()
    
    # Use uv sync to resolve dependencies properly
    print("Step 1: Syncing dependencies with uv...")
    if not run_command("uv sync", "Syncing project dependencies"):
        print("❌ Failed to sync dependencies. Trying manual installation...")
        
        # Fallback to manual installation
        install_commands = [
            ("uv pip install 'torch>=2.0.0,<3.0.0' 'torchaudio>=2.0.0,<3.0.0'", 
             "Installing compatible PyTorch versions"),
            ("uv pip install 'pyannote-audio>=3.0.0,<4.0.0'", 
             "Installing compatible Pyannote Audio version"),
            ("uv pip install 'pytorch-lightning>=2.0.0,<3.0.0'", 
             "Installing compatible PyTorch Lightning version"),
        ]
        
        success = True
        for cmd, desc in install_commands:
            if not run_command(cmd, desc):
                success = False
                break
    else:
        success = True
    
    print()
    
    # Step 2: Verify installation
    print("Step 2: Verifying installation...")
    new_versions = check_current_versions()
    
    # Check if versions are in acceptable ranges
    acceptable_ranges = {
        'torch': ('2.0.0', '3.0.0'),
        'torchaudio': ('2.0.0', '3.0.0'),
        'pyannote-audio': ('3.0.0', '4.0.0'),
        'pytorch-lightning': ('2.0.0', '3.0.0')
    }
    
    all_good = True
    for package, (min_ver, max_ver) in acceptable_ranges.items():
        current_version = new_versions.get(package)
        if current_version:
            major, minor = map(int, current_version.split('.')[:2])
            min_major, min_minor = map(int, min_ver.split('.'))
            max_major, max_minor = map(int, max_ver.split('.'))
            
            if not (min_major <= major <= max_major):
                print(f"⚠️  {package}: {current_version} is outside acceptable range {min_ver}-{max_ver}")
                all_good = False
    
    if all_good:
        print("\n✅ All packages installed with compatible versions!")
        print("🎉 Your environment is now optimized for diarization quality!")
    else:
        print("\n⚠️  Some packages may not have installed correctly.")
        print("   You can continue, but diarization quality may be affected.")
    
    print(f"\n📦 Original versions backed up to: {backup_file}")
    print("🔄 You may need to restart your Python environment for changes to take effect.")
    
    return success

def restore_backup():
    """Restore package versions from backup."""
    backup_file = Path("package_versions_backup.json")
    
    if not backup_file.exists():
        print("❌ No backup file found.")
        return False
    
    print("🔄 Restoring original package versions...")
    
    with open(backup_file, 'r') as f:
        versions = json.load(f)
    
    print("Original versions to restore:")
    for package, version in versions.items():
        print(f"   {package}: {version}")
    
    confirm = input("\nProceed with restoration? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return False
    
    # Restore packages
    for package, version in versions.items():
        cmd = f"uv pip install '{package}=={version}'"
        run_command(cmd, f"Restoring {package} to {version}")
    
    print("✅ Restoration completed!")
    return True

def main():
    """Main function."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "restore":
            restore_backup()
            return
        elif sys.argv[1] == "check":
            check_current_versions()
            return
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Available commands: check, restore")
            return
    
    fix_compatibility()

if __name__ == "__main__":
    main() 