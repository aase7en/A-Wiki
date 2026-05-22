"""greet — Multi-language greeting CLI utility.

Usage:
    python greet.py                          # Hello, World!
    python greet.py --name Alice             # Hello, Alice!
    python greet.py --lang th --name น้อง    # Thai greeting
    python greet.py --lang jp --name 田中    # Japanese greeting
"""
import argparse
import sys
import io

# Force UTF-8 on Windows to handle Unicode characters (Thai, Japanese, etc.)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

GREETINGS = {
    "en": "Hello",
    "th": "สวัสดี",
    "jp": "こんにちは",
}


def greet(name: str, lang: str) -> str:
    """Return a localized greeting string."""
    greeting = GREETINGS.get(lang)
    if greeting is None:
        supported = ", ".join(sorted(GREETINGS.keys()))
        print(
            f"error: unsupported language '{lang}'. Supported: {supported}",
            file=sys.stderr,
        )
        sys.exit(1)
    return f"{greeting}, {name}!"


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-language greeting CLI")
    parser.add_argument(
        "--name",
        default="World",
        help="Name to greet (default: World)",
    )
    parser.add_argument(
        "--lang",
        default="en",
        choices=list(GREETINGS.keys()),
        help="Language code for greeting",
    )
    args = parser.parse_args()

    message = greet(name=args.name, lang=args.lang)
    print(message)


if __name__ == "__main__":
    main()