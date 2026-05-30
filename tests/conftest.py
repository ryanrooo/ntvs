"""Shared pytest configuration.

Puts ``code/`` on ``sys.path`` so test modules can ``import api`` and
``from services... import ...`` exactly as the application does. Individual
test files keep their own ``sys.path.insert`` for parity with the existing
suite, but this makes new tests work without the boilerplate.
"""
import sys
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
