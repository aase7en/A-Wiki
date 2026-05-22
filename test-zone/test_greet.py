"""
IRON LAW #1 — TESTS BEFORE CODE.

All tests MUST FAIL before greet.py exists.
Run: python -m pytest test-zone/test_greet.py -v
"""

import subprocess
import sys


def run_greet(*args):
    """Helper: run greet.py with arguments and return (stdout, stderr, exit_code).
    
    Uses UTF-8 encoding to handle Thai, Japanese, and other Unicode characters
    across subprocess boundaries on Windows.
    """
    result = subprocess.run(
        [sys.executable, "test-zone/greet.py", *args],
        capture_output=True,
        encoding="utf-8",
    )
    out = result.stdout.strip() if result.stdout else ""
    err = result.stderr.strip() if result.stderr else ""
    return out, err, result.returncode


class TestDefaultGreeting:
    """No arguments -> prints 'Hello, World!'"""

    def test_default_greeting(self):
        out, err, code = run_greet()
        assert code == 0, f"Expected exit 0, got {code}: {err}"
        assert out == "Hello, World!", f"Expected 'Hello, World!', got '{out}'"


class TestNameGreeting:
    """--name argument -> prints 'Hello, <name>!'"""

    def test_name_greeting(self):
        out, err, code = run_greet("--name", "Alice")
        assert code == 0, f"Expected exit 0, got {code}: {err}"
        assert out == "Hello, Alice!", f"Expected 'Hello, Alice!', got '{out}'"


class TestThaiGreeting:
    """--lang th -> prints Thai greeting"""

    def test_thai_greeting(self):
        out, err, code = run_greet("--lang", "th")
        assert code == 0, f"Expected exit 0, got {code}: {err}"
        assert "สวัสดี" in out, f"Expected Thai greeting, got '{out}'"

    def test_thai_greeting_with_name(self):
        out, err, code = run_greet("--lang", "th", "--name", "น้อง")
        assert code == 0, f"Expected exit 0, got {code}: {err}"
        assert out == "สวัสดี, น้อง!", f"Expected 'สวัสดี, น้อง!', got '{out}'"


class TestJapaneseGreeting:
    """--lang jp -> prints Japanese greeting"""

    def test_japanese_greeting(self):
        out, err, code = run_greet("--lang", "jp")
        assert code == 0, f"Expected exit 0, got {code}: {err}"
        assert "こんにちは" in out, f"Expected Japanese greeting, got '{out}'"

    def test_japanese_greeting_with_name(self):
        out, err, code = run_greet("--lang", "jp", "--name", "田中")
        assert code == 0, f"Expected exit 0, got {code}: {err}"
        assert out == "こんにちは, 田中!", f"Expected 'こんにちは, 田中!', got '{out}'"


class TestInvalidLanguage:
    """--lang with unsupported language -> non-zero exit + error message"""

    def test_invalid_language(self):
        out, err, code = run_greet("--lang", "fr")
        assert code != 0, f"Expected non-zero exit for invalid lang, got {code}"
        assert "unsupported" in err.lower() or "invalid" in err.lower(), (
            f"Expected error message about unsupported language, got: '{err}'"
        )