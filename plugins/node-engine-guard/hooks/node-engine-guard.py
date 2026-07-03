#!/usr/bin/env python3
from pathlib import Path
import sys


plugin_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(plugin_root / "src"))

from node_engine_guard.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
