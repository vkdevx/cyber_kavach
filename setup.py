#!/usr/bin/env python3
"""
CyberKavach Auto Setup Script
Works on Windows, Linux and macOS
Run: python setup.py
"""
import os
import sys
import subprocess
import shutil
import platform

def print_header():
    print("\n" + "=" * 52)
    print("  CYBERKAVACH - SIH26145 Auto Setup")
    print("  AI-Based Cyber Threat Detection System")
    print("=" * 52 + "\n")

def run(cmd, check=True, capture=False):
    return subprocess.run(cmd, shell=True, check=check,
                          capture_output=capture, text=True)

def main():
    print_header()
    is_windows = platform.system() == "Windows"
    venv_python = r"venv\Scripts\python.exe" if is_windows else "venv/bin/python"
    venv_pip = r"venv\Scripts\pip.exe" if is_windows else "venv/bin/pip"

    # Step 1 — Check Python version
    print("[1/5] Checking Python version...")
    ver = sys.version_info
    if ver.major < 3 or (ver.major == 3 and ver.minor < 10):
        print(f"      ERROR: Python 3.10+ required. You have {ver.major}.{ver.minor}")
        print("      Download from: https://python.org/downloads")
        sys.exit(1)
    print(f"      Python {ver.major}.{ver.minor}.{ver.micro} — OK\n")

    # Step 2 — Create venv
    print("[2/5] Setting up virtual environment...")
    if not os.path.exists("venv"):
        run(f"{sys.executable} -m venv venv")
        print("      Virtual environment created.\n")
    else:
        print("      Already exists. Skipping.\n")

    # Step 3 — Install dependencies
    print("[3/5] Installing dependencies (may take 2-3 min)...")
    run(f"{venv_pip} install --upgrade pip --quiet")
    run(f"{venv_pip} install -r requirements.txt")
    print("      All packages installed.\n")

    # Step 4 — Create .env
    print("[4/5] Configuring environment...")
    if not os.path.exists(".env"):
        shutil.copy(".env.example", ".env")
        print("      Created .env from template.")
        if is_windows:
            print("      TIP: Open .env and set CAPTURE_INTERFACE=Wi-Fi")
        else:
            print("      TIP: Open .env and set CAPTURE_INTERFACE=eth0 (or wlan0)")
    else:
        print("      .env already exists. Skipping.")
    print()

    # Step 5 — Done
    print("[5/5] Setup complete!")
    print()
    print("=" * 52)
    print("  HOW TO RUN:")
    if is_windows:
        print("    python run_server.py")
        print("    OR double-click: run_server.bat")
        print()
        print("  NOTE: Run as Administrator for packet capture.")
    else:
        print("    sudo python run_server.py")
    print()
    print("  Dashboard: http://localhost:8000")
    print("=" * 52 + "\n")

if __name__ == "__main__":
    main()
