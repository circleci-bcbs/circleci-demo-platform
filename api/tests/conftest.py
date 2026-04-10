"""Shared fixtures for API tests."""

import sys
import os
import pytest

# Ensure project root is importable.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from api.app import app, ITEMS


@pytest.fixture
def client():
    """Create a Flask test client with a fresh item store."""
    app.config["TESTING"] = True
    # Snapshot and restore ITEMS so tests are isolated.
    original = dict(ITEMS)
    with app.test_client() as client:
        yield client
    ITEMS.clear()
    ITEMS.update(original)
