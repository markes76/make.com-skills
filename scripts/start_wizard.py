#!/usr/bin/env python3
"""Run the Make Skills companion directly from a GitHub clone or release zip."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from make_skills.cli import main  # noqa: E402


if __name__ == "__main__":
    main(sys.argv[1:])
