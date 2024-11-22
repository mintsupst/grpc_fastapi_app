import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fastapi_client import app
from file_transfer_pb2 import EmptyRequest, FileListResponse


client = TestClient(app)

@pytest.fixture
def mock_grpc_stub(mocker):
    # Mock the gRPC stub
    grpc_stub_mock = mocker.patch("fastapi_client.grpc_stub")
    grpc_stub_mock.ListFiles = mocker.AsyncMock()
    return grpc_stub_mock

def test_list_files_success(mock_grpc_stub):
    """Test the list_files endpoint for successful response."""
    # Mock the gRPC response
    mock_grpc_stub.ListFiles.return_value = FileListResponse(
        filenames=["file1.txt", "file2.png"]
    )

    # Make the request to the FastAPI endpoint
    response = client.get("/files/")
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == {"filenames": ["file1.txt", "file2.png"]}
