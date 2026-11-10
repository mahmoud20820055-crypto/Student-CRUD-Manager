import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import create_app  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    app = create_app({"DATABASE_PATH": str(tmp_path / "test.db"), "TESTING": True})
    return app.test_client()


@pytest.fixture()
def student():
    return {
        "student_code": "S-1001",
        "first_name": "Sara",
        "last_name": "Ahmed",
        "email": "sara.ahmed@example.com",
        "major": "Computer Science",
        "gpa": 3.7,
        "enrolled_year": 2023,
    }
