"""
CuraFrame Console Launcher

This script launches the CuraFrame Streamlit console from the project root.

Purpose:
    - Single, reproducible entry point for the UI
    - No application logic
    - No constraint reasoning
    - No configuration decisions

Usage:
    python launch_console.py
    
    Or with Streamlit arguments:
    python launch_console.py --server.port 8502

Philosophy:
    This is a convenience wrapper only.
    All logic lives in cura_frame (core) and apps/console_streamlit (UI).
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Launch the CuraFrame Streamlit console."""
    
    # Locate app.py relative to this script
    script_dir = Path(__file__).parent
    app_path = script_dir / "apps" / "console_streamlit" / "app.py"
    
    # Verify app.py exists
    if not app_path.exists():
        print(f"Error: Could not find Streamlit app at {app_path}", file=sys.stderr)
        print(f"Expected path: {app_path.absolute()}", file=sys.stderr)
        sys.exit(1)
    
    # Check if streamlit is available
    try:
        result = subprocess.run(
            [sys.executable, "-m", "streamlit", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            raise FileNotFoundError
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(
            "Error: Streamlit is not installed or not accessible.\n"
            "Install it with: pip install streamlit",
            file=sys.stderr
        )
        sys.exit(1)
    
    # Build command
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    
    # Forward any CLI arguments (e.g., --server.port 8502)
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    # Display launch message
    print(f"Launching CuraFrame Console...")
    print(f"App: {app_path.relative_to(script_dir)}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    # Launch Streamlit
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\nError: Streamlit exited with code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\nShutdown requested by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
