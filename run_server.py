import os
import sys
import subprocess
from pathlib import Path

# Ensure working directory is project root
ROOT_DIR = Path(__file__).resolve().parent
os.chdir(ROOT_DIR)

def main():
    print("=" * 65)
    print("   🛡️ CYBERKAVACH (SIH26145) — AI THREAT DETECTION & DEFENCE SYSTEM")
    print("=" * 65)
    print(f"[*] Project Directory: {ROOT_DIR}")

    # Locate virtual environment uvicorn
    venv_uvicorn = ROOT_DIR / "venv" / "Scripts" / "uvicorn.exe"
    venv_python = ROOT_DIR / "venv" / "Scripts" / "python.exe"

    if venv_uvicorn.exists():
        executable = str(venv_uvicorn)
        cmd = [executable, "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    elif venv_python.exists():
        cmd = [str(venv_python), "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    else:
        cmd = [sys.executable, "-m", "uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

    print(f"[*] Launching Command: {' '.join(cmd)}")
    print("[*] Dashboard URL:     http://localhost:8000")
    print("[*] Passive Sniffer:   Active (Wi-Fi Promiscuous Mode)")
    print("[*] Press Ctrl+C to stop the server.")
    print("-" * 65)

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n[*] CyberKavach server stopped.")
    except Exception as e:
        print(f"\n[!] Server stopped with status: {e}")

if __name__ == "__main__":
    main()
