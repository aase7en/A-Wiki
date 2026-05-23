#!/usr/bin/env python3
import os
import sys
import subprocess
import shutil

def main():
    if len(sys.argv) < 2:
        print("Usage: python hooks_runner.py <hook_name>")
        sys.exit(1)

    hook_name = sys.argv[1]
    # Normalize naming: change dash to underscore for python files if needed
    py_hook_name = hook_name.replace("-", "_")
    
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # 1. Look for Python hook first
    py_hook_path = os.path.join(repo_root, "scripts", "hooks", f"{py_hook_name}.py")
    if os.path.exists(py_hook_path):
        # Read all stdin to forward
        stdin_data = sys.stdin.read()
        
        # Run Python hook
        result = subprocess.run(
            [sys.executable, py_hook_path],
            input=stdin_data,
            text=True,
            capture_output=True
        )
        # Forward outputs
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        sys.exit(result.returncode)

    # 2. Look for Bash hook as fallback
    # Look in .claude/hooks/ or .gemini/hooks/
    bash_hook_path = os.path.join(repo_root, ".claude", "hooks", f"{hook_name}.sh")
    if not os.path.exists(bash_hook_path):
        bash_hook_path = os.path.join(repo_root, ".gemini", "hooks", f"{hook_name}.sh")
        
    if os.path.exists(bash_hook_path):
        # We need bash to run .sh files
        bash_exe = shutil.which("bash")
        if not bash_exe:
            # On Windows, check common git bash locations
            git_bash = r"C:\Program Files\Git\bin\bash.exe"
            if os.path.exists(git_bash):
                bash_exe = git_bash
                
        if bash_exe:
            stdin_data = sys.stdin.read()
            result = subprocess.run(
                [bash_exe, bash_hook_path],
                input=stdin_data,
                text=True,
                capture_output=True
            )
            if result.stdout:
                sys.stdout.write(result.stdout)
            if result.stderr:
                sys.stderr.write(result.stderr)
            sys.exit(result.returncode)
        else:
            # No bash found, skip hook to avoid blocking the user
            print(f"Warning: Hook {hook_name} skipped because 'bash' was not found on this system.", file=sys.stderr)
            sys.exit(0)
            
    print(f"Error: Hook {hook_name} (Python or Bash) not found.", file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    main()
