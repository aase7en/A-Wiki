#!/usr/bin/env python3
"""
A-Wiki Dashboard Admin Password Manager
=========================================
Set or reset the admin password for A-Wiki Live Dashboard.
Password is stored as SHA-256 hash in .tmp/admin-password.hash
(Simple hash sufficient for local dev; upgrade to bcrypt for production).

Usage:
  python3 scripts/set-admin-password.py              # Interactive prompt
  python3 scripts/set-admin-password.py --set "pass" # Set from CLI
  python3 scripts/set-admin-password.py --reset      # Remove password
  python3 scripts/set-admin-password.py --status     # Check if set
"""
import sys
import hashlib
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PASSWORD_FILE = REPO_ROOT / ".tmp" / "admin-password.hash"


def hash_password(password: str, salt: str = "") -> str:
    """Simple salted SHA-256 hash."""
    if not salt:
        salt = os.urandom(16).hex()
    return f"{salt}:{hashlib.sha256((salt + password).encode()).hexdigest()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify password against stored hash."""
    if ":" not in stored:
        return False
    salt, hash_val = stored.split(":", 1)
    return hash_password(password, salt).split(":", 1)[1] == hash_val


def set_password(password: str):
    """Set admin password."""
    PASSWORD_FILE.parent.mkdir(parents=True, exist_ok=True)
    h = hash_password(password)
    PASSWORD_FILE.write_text(h)
    PASSWORD_FILE.chmod(0o600)
    print(f"✅ Admin password set → {PASSWORD_FILE}")


def reset_password():
    """Remove admin password."""
    if PASSWORD_FILE.exists():
        PASSWORD_FILE.unlink()
        print("🗑️  Admin password removed — FREE-ONLY mode active")
    else:
        print("ℹ️  No password was set")


def check_status():
    """Check if password is set."""
    if PASSWORD_FILE.exists():
        print(f"🔒 Admin password IS set ({PASSWORD_FILE})")
    else:
        print("🔓 No admin password — FREE-ONLY mode (paid models disabled)")


def main():
    if len(sys.argv) < 2 or sys.argv[1] == "--status":
        check_status()
    elif sys.argv[1] == "--set" and len(sys.argv) > 2:
        set_password(sys.argv[2])
    elif sys.argv[1] == "--set":
        import getpass
        pw = getpass.getpass("Enter admin password: ")
        pw2 = getpass.getpass("Confirm: ")
        if pw != pw2:
            print("❌ Passwords do not match")
            sys.exit(1)
        if len(pw) < 4:
            print("❌ Password too short (min 4 chars)")
            sys.exit(1)
        set_password(pw)
    elif sys.argv[1] == "--reset":
        reset_password()
    elif sys.argv[1] == "--check":
        # Non-zero exit if no password set
        if not PASSWORD_FILE.exists():
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
