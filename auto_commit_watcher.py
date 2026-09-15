#!/usr/bin/env python3
"""
CyberKavach - Real-Time Automated GitHub Synchronizer (Watchdog)
Automatically tracks file modifications, stages changes, commits with 
informative timestamps, and pushes to remote GitHub repository.

Features:
- Debouncing (prevents push storms on rapid successive edits)
- Respects ignored files (.git, .env, *.db, venv, __pycache__, logs)
- Clean console feedback with color status indicators
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Patterns / paths to completely ignore
IGNORED_PATTERNS = [
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".cloudflared",
    "oneway_sentinel.db",
    "oneway_sentinel.db-shm",
    "oneway_sentinel.db-wal",
    ".env",
    "logs",
    ".tmp",
    ".swp"
]

class AutoGitSyncHandler(FileSystemEventHandler):
    def __init__(self, debounce_seconds: float = 3.0):
        super().__init__()
        self.debounce_seconds = debounce_seconds
        self.lock = threading.Lock()
        self.timer: threading.Timer = None
        self.pending_files = set()

    def _is_ignored(self, path: str) -> bool:
        norm_path = path.replace("\\", "/")
        for pat in IGNORED_PATTERNS:
            if f"/{pat}/" in norm_path or norm_path.endswith(f"/{pat}") or norm_path.endswith(pat):
                return True
            if pat in norm_path.split("/"):
                return True
        if norm_path.endswith((".pyc", ".db", ".sqlite", ".log", ".tmp", ".swp")):
            return True
        return False

    def on_any_event(self, event):
        if event.is_directory:
            return
        if self._is_ignored(event.src_path):
            return

        # Track file and schedule debounced sync
        with self.lock:
            rel_path = os.path.relpath(event.src_path, os.getcwd())
            self.pending_files.add(rel_path)
            
            if self.timer:
                self.timer.cancel()
            
            self.timer = threading.Timer(self.debounce_seconds, self._perform_sync)
            self.timer.daemon = True
            self.timer.start()

    def _perform_sync(self):
        with self.lock:
            if not self.pending_files:
                return
            changed_summary = ", ".join(list(self.pending_files)[:3])
            if len(self.pending_files) > 3:
                changed_summary += f" and {len(self.pending_files) - 3} more"
            self.pending_files.clear()

        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[🔄 GIT AUTO-SYNC] {now_str} — Detected changes in: {changed_summary}")

        try:
            # Check if git status has changes
            status_res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if not status_res.stdout.strip():
                print("   └── No actual git changes detected. Skipping.")
                return

            print("   ├── Staging modified files...")
            subprocess.run(["git", "add", "."], check=True)

            commit_msg = f"auto(sync): update {changed_summary} [{now_str}]"
            print(f"   ├── Committing: \"{commit_msg}\"")
            commit_res = subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True, text=True)
            
            if commit_res.returncode == 0:
                print("   ├── Pushing to GitHub (origin main)...")
                push_res = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
                if push_res.returncode == 0:
                    print(f"   └── ✅ Successfully synchronized with GitHub at {now_str}!\n")
                else:
                    print(f"   └── ⚠️ Push notice: {push_res.stderr.strip() or push_res.stdout.strip()}")
            else:
                print(f"   └── Commit output: {commit_res.stdout.strip()}")

        except Exception as err:
            print(f"   └── ❌ Git sync error: {err}")


def main():
    root_dir = os.path.abspath(".")
    print("=" * 60)
    print("  🛡️  CyberKavach Auto-Git Synchronizer Active")
    print(f"  📂  Watching Directory: {root_dir}")
    print("  ⏱️  Debounce Interval: 3.0 seconds")
    print("  🚀  Changes will be automatically committed & pushed.")
    print("  🛑  Press Ctrl+C to stop.")
    print("=" * 60)

    event_handler = AutoGitSyncHandler(debounce_seconds=3.0)
    observer = Observer()
    observer.schedule(event_handler, path=root_dir, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping auto-git synchronizer...")
        observer.stop()
    observer.join()
    print("Synchronizer stopped.")


if __name__ == "__main__":
    main()
