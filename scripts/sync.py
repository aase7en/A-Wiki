#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import socket
import argparse

# Configuration: sync only tracked knowledge/config surfaces.
SYNC_PATHS = [
    "wiki",
    "docs",
    "decisions",
    "journal",
    "log.md",
    "index.md",
    "index-ai.md",
    "index-env.md",
    "index-iot.md",
    "index-it.md",
    "index-pharmacy.md",
    "CLAUDE.md",
    "GEMINI.md",
    "AGENTS.md",
    ".clinerules",
    ".cursorrules",
    ".windsurfrules",
    ".github/copilot-instructions.md",
    "brain-map.canvas",
]
EXCLUDE_DIRS = [".git", ".obsidian", ".claude", ".gemini", ".codex", "raw", "__pycache__", "node_modules"]

def get_device_name():
    # Environment variable overrides everything
    env_name = os.environ.get("WIKI_DEVICE_NAME", "").strip()
    if env_name:
        return env_name

    # Custom device file (e.g. ~/.wiki-device)
    try:
        home = os.path.expanduser("~")
        device_file = os.path.join(home, ".wiki-device")
        if os.path.exists(device_file):
            with open(device_file, "r", encoding="utf-8") as f:
                return f.read().strip()
    except Exception:
        pass

    # Fallback to hostname
    return socket.gethostname().split(".")[0]

def run_cmd(args, check=True):
    try:
        result = subprocess.run(args, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else "", e.returncode

def is_repo_dirty():
    # Check if git status has any changes in SYNC_PATHS or root index files
    out, _, _ = run_cmd(["git", "status", "--porcelain"])
    if not out:
        return False
    
    for line in out.splitlines():
        if len(line) < 4:
            continue
        filepath = line[3:]
        # Check if the modified file starts with any of our sync paths
        for path in SYNC_PATHS:
            if filepath.startswith(path) or path.startswith(filepath):
                return True
    return False

def sync_now(device):
    print(f"[{time.strftime('%H:%M:%S')}] Starting sync on device: {device}...")
    
    # 1. Fetch remote updates first
    run_cmd(["git", "fetch", "origin", "main"])
    
    # 2. Check if local is dirty
    dirty = is_repo_dirty()
    stashed = False
    
    if dirty:
        print("Local changes detected. Stashing...")
        run_cmd(["git", "stash", "push", "-m", f"sync-stash-{device}"])
        stashed = True
        
    # 3. Pull from remote with rebase
    # In case of conflict, we prefer 'theirs' (our local changes being rebased onto remote)
    print("Pulling remote changes with rebase...")
    stdout, stderr, code = run_cmd(["git", "pull", "--rebase", "-Xtheirs", "origin", "main"], check=False)
    
    if code != 0:
        print(f"ERROR pulling from remote: {stderr}")
        print("Attempting to abort rebase...")
        run_cmd(["git", "rebase", "--abort"], check=False)
        if stashed:
            run_cmd(["git", "stash", "pop"], check=False)
        return False
        
    # 4. Pop stash if we stashed
    if stashed:
        print("Popping stashed changes...")
        stdout, stderr, code = run_cmd(["git", "stash", "pop"], check=False)
        if code != 0:
            print(f"Conflict encountered while popping stash: {stderr}")
            print("Please resolve conflicts manually in the git repository.")
            return False
            
    # 5. Commit and push local changes if any
    if is_repo_dirty():
        print("Staging changes...")
        for path in SYNC_PATHS:
            if os.path.exists(path):
                run_cmd(["git", "add", path])
                
        commit_msg = f"sync({device}): auto-sync changes at {time.strftime('%Y-%m-%d %H:%M:%S')}"
        print(f"Committing: {commit_msg}")
        run_cmd(["git", "commit", "-m", commit_msg])
        
        print("Pushing to remote...")
        stdout, stderr, code = run_cmd(["git", "push", "origin", "main"], check=False)
        if code != 0:
            print(f"ERROR pushing to remote: {stderr}")
            return False
        print("Push successful!")
    else:
        print("No local changes to push.")
        
    print("Sync completed successfully.")
    return True

def get_max_mtime():
    # Find the maximum modification time of tracked files
    max_time = 0.0
    for root, dirs, files in os.walk("."):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            filepath = os.path.join(root, file)
            # Normalize path to forward slashes for cross-platform comparison
            norm_path = filepath.replace("\\", "/").lstrip("./")
            
            # Check if this file is in our sync paths
            match = False
            for path in SYNC_PATHS:
                if norm_path.startswith(path):
                    match = True
                    break
            
            if match:
                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime > max_time:
                        max_time = mtime
                except Exception:
                    pass
    return max_time

def daemon_mode(device, interval=10, debounce=5):
    print(f"Daemon mode started. Scanning every {interval}s (debounce {debounce}s)...")
    last_mtime = get_max_mtime()
    
    # Run initial sync on startup
    sync_now(device)
    
    try:
        while True:
            time.sleep(interval)
            current_mtime = get_max_mtime()
            
            if current_mtime > last_mtime:
                print(f"[{time.strftime('%H:%M:%S')}] Change detected! Debouncing for {debounce}s...")
                time.sleep(debounce)
                
                # Verify that no more edits occurred during debounce
                check_mtime = get_max_mtime()
                if check_mtime > current_mtime:
                    print("Files are still being edited, waiting next tick...")
                    continue
                    
                # Sync changes
                success = sync_now(device)
                if success:
                    last_mtime = get_max_mtime()
                else:
                    # If sync failed, keep last_mtime so we try again next tick
                    print("Sync failed, will retry on next change or tick.")
            else:
                # Periodic pull even if no local changes, to keep device up-to-date
                # Pull every 5 minutes (300 seconds)
                now = time.time()
                if int(now) % 300 < interval:
                    print(f"[{time.strftime('%H:%M:%S')}] Periodic remote check...")
                    run_cmd(["git", "fetch", "origin", "main"])
                    out, _, _ = run_cmd(["git", "log", "HEAD..origin/main", "--oneline"])
                    if out:
                        print("Remote updates found. Syncing...")
                        sync_now(device)
                        last_mtime = get_max_mtime()
    except KeyboardInterrupt:
        print("\nDaemon stopped by user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cross-platform Git Sync script for A-Wiki.")
    parser.add_argument("--daemon", action="store_true", help="Run in background daemon mode")
    parser.add_argument("--interval", type=int, default=10, help="Scan interval for daemon mode in seconds")
    parser.add_argument("--debounce", type=int, default=5, help="Debounce interval in seconds")
    parser.add_argument("--now", action="store_true", help="Sync immediately and exit")
    
    args = parser.parse_args()
    device = get_device_name()
    
    # Ensure we are in a git repository
    if not os.path.exists(".git"):
        print("ERROR: Must run from the root of a git repository.")
        sys.exit(1)
        
    if args.daemon:
        daemon_mode(device, interval=args.interval, debounce=args.debounce)
    elif args.now or not len(sys.argv) > 1:
        success = sync_now(device)
        sys.exit(0 if success else 1)
