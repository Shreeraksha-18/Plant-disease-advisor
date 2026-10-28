import os
import tempfile
from pathlib import Path

# Use a throwaway database and the built-in explanations, so tests never touch app.db or call Gemini.
# These must be set BEFORE src.app is imported.
_db = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_db.as_posix()}"
os.environ["USE_LLM"] = "false"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    from src.app import app

    with TestClient(app) as c:
        yield c