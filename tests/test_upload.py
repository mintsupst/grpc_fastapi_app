from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi_client import app

client = TestClient(app)

def test_upload_file_success(tmp_path):
    file_content = b"Hello, this is a test file!"
    test_file = tmp_path / "test_file.txt"
    test_file.write_bytes(file_content)

    with open(test_file, "rb") as file:
        response = client.post("/upload/", files={"file": ("test_file.txt", file, "text/plain")})

    assert response.status_code == 200
    assert "message" in response.json()
