"""Load KEY=VALUE pairs from a local .env file (never committed). Does not override existing env vars."""
import os
from pathlib import Path


def load_env(path: Path) -> bool:
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8-sig").splitlines():  # utf-8-sig: tolerate Notepad BOM
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return True
