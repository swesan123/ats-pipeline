"""FastAPI dependencies."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from functools import lru_cache
from src.db.database import Database


@lru_cache()
def get_db() -> Database:
    """Get database instance (singleton)."""
    return Database()
