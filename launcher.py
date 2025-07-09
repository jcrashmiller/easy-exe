#!/usr/bin/env python3
"""
Easy EXE Launcher
This script handles launching Easy EXE with proper error handling for missing dependencies
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Ensure we have Python 3.7+"""
    if sys.version_info < (3, 7):
        print("❌ Easy EXE requires Python 3.7 or later")
        print(f"   Current version: {sys.version}")
        sys.exit(1)

def install_requirements():
    """Install required Python packages"""
    requirements_file = Path(__file__).parent / "requirements.txt"

    if requirements_file.exists():
        print("📦 Installing Python dependencies from requirements.txt...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True, capture_output=True, text=True)
            print("✅ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Requirements file installation failed:")
            print(f"   Exit code: {e.returncode}")
            if e.stderr:
                print(f"   Error: {e.stderr}")
            print("\n🔄 Trying individual package installation...")
            return install_minimal_requirements()
    else:
        print("⚠️  Requirements file not found")
        print("🔄 Installing packages individually...")
        return install_minimal_requirements()
    """Install just the core requirements one by one"""
    core_packages = ["requests", "beautifulsoup4", "lxml"]
    optional_packages = ["PyQt6"]

    print("📦 Installing core dependencies...")
    success_count = 0

    for package in core_packages:
        try:
            print(f"   Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            success_count += 1
            print(f"   ✅ {package} installed")
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to install {package}")

    print(f"\n📦 Installing GUI dependencies...")
    gui_success = False

    for package in optional_packages:
        try:
            print(f"   Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True)
            gui_success = True
            print(f"   ✅ {package} installed - GUI mode available!")
            break
        except subprocess.CalledProcessError:
            print(f"   ❌ Failed to install {package}")

    if not gui_success:
        print("   💡 GUI will not be available, but CLI mode will work")

    return success_count >= 2  # Need at least requests and beautifulsoup4

def check_gui_availability():
    """Check if GUI components are available"""
    try:
        import PyQt6
        # Check if we have a display
        if os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'):
            return True
        else:
            print("💡 No display detected - running in CLI mode")
            return False
    except ImportError:
        print("💡 PyQt6 not available - running in CLI mode")
        return False

def main():
    """Main launcher function"""
    check_python_version()

    # Determine script location
    script_dir = Path(__file__).parent
    main_script = script_dir / "easy_exe.py"

    if not main_script.exists():
        print(f"❌ Main script not found: {main_script}")
        sys.exit(1)

    # Check if this is the first run
    cache_dir = Path.home() / ".cache" / "easy-exe"
    first_run_marker = cache_dir / ".first_run_complete"

    if not first_run_marker.exists():
        print("🎉 Welcome to Easy EXE!")
        print("   Setting up for first use...")

        # Try to install requirements
        if install_requirements():
            print("   GUI mode will be available")

        # Create marker file
        cache_dir.mkdir(parents=True, exist_ok=True)
        first_run_marker.touch()
        print("   Setup complete!\n")

    # Check GUI availability
    gui_available = check_gui_availability()

    # Prepare command line arguments
    cmd = [sys.executable, str(main_script)]

    # Add CLI flag if GUI is not available
    if not gui_available:
        cmd.append('--cli')

    # Pass through all command line arguments
    cmd.extend(sys.argv[1:])

    # Launch Easy EXE
    try:
        # For AppImage usage, we want to replace the current process
        # This ensures clean process handling and proper exit codes
        os.execv(sys.executable, cmd)
    except Exception as e:
        print(f"❌ Failed to launch Easy EXE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
