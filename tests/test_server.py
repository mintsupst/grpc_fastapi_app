import os, sys, pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from grpc_server import FileService
from file_transfer_pb2 import EmptyRequest, FileListResponse



@pytest.fixture
def setup_files(tmp_path):
    """Setup temporary files for testing."""
    file_dir = tmp_path / "files"
    file_dir.mkdir()
    (file_dir / "file1.txt").write_text("content1")
    (file_dir / "file2.txt").write_text("content2")
    return file_dir


@pytest.mark.asyncio
async def test_list_files_success(setup_files):
    """Test ListFiles method when files are available."""
    # Initialize the service
    service = FileService()
    service.directory = str(setup_files)  # Point to the temporary directory
    service.filenames = os.listdir(setup_files)
 
    # Call the ListFiles method
    response = await service.ListFiles(EmptyRequest(), None)
 
    # Assert response
    assert isinstance(response, FileListResponse)
    assert sorted(response.filenames) == sorted(["file1.txt", "file2.txt"])


@pytest.mark.asyncio
async def test_list_files_not_found():
    """Test ListFiles method when no files are available."""
    # Initialize the service with an empty directory
    service = FileService()
    service.directory = "empty_directory"
    os.makedirs(service.directory, exist_ok=True)
    service.filenames = []

    # Call the ListFiles method
    response = await service.ListFiles(EmptyRequest(), None)

    # Assert response
    assert isinstance(response, FileListResponse)
    assert len(response.filenames) == 0
