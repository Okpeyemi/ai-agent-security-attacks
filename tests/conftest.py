import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SDK_DIR = REPO_ROOT / "sdk"
for p in (str(REPO_ROOT), str(SDK_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)
