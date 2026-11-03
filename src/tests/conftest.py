import os
import pytest
from app import create_app

@pytest.fixture()
def app(tmp_path):
    database = tmp_path / "test.sqlite3"
    uploads = tmp_path / "uploads"
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "DATABASE": str(database),
        "UPLOAD_FOLDER": str(uploads),
        "MAX_CONTENT_LENGTH": 10 * 1024 * 1024,
    })
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()
