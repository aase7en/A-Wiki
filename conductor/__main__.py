import sys

from .cli import main

# Locale pipes (Thai-Windows cp874 etc.) crash printing ✅/Thai status
# output; pin pipes to UTF-8 like scripts/hooks_runner.py does.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass

sys.exit(main())
