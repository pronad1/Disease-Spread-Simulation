"""
conftest.py — pytest configuration for EpiSim tests.
Inserts the project root into sys.path so `episim` is always importable,
regardless of which directory pytest is invoked from.
"""
import sys
from pathlib import Path

# Project root is one level up from the tests/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
