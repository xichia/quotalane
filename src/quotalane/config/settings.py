from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB_PATH = Path(os.getenv("QUOTALANE_DB_PATH", ".quotalane/quotalane.sqlite"))
