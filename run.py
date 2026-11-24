"""
Cross-platform launcher for Farmer Carbon Tracker.
Works on Windows, Linux, and macOS.

Usage:
    python run.py
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
REQUIREMENTS = BACKEND / "requirements.txt"


def main() -> int:
    if not BACKEND.exists():
        print(f"❌ backend folder not found at {BACKEND}")
        return 1

    if not (BACKEND / "main.py").exists():
        print(f"❌ backend/main.py not found at {BACKEND / 'main.py'}")
        return 1

    # 1. Install dependencies
    if REQUIREMENTS.exists():
        print("📦 Installing dependencies...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
        )
    else:
        print("⚠️  requirements.txt not found, skipping install")

    # 2. Start uvicorn from inside backend/
    print("🚀 Starting server at http://localhost:8000")
    print("   Docs:   http://localhost:8000/docs")
    print("   Press Ctrl+C to stop\n")
    os.chdir(BACKEND)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "uvicorn", "main:app",
             "--reload", "--port", "8000"]
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())