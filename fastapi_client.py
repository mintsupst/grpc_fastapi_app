from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from grpc.aio import insecure_channel
from file_transfer_pb2_grpc import FileServiceStub
from file_transfer_pb2 import FileRequest, FileChunk, EmptyRequest 
import grpc
import traceback

app = FastAPI()

# Create a persistent gRPC channel and stub
grpc_channel = insecure_channel("file-transfer_grpc-server_1:50051") #
grpc_stub = FileServiceStub(grpc_channel)


@app.get("/files/")
async def list_files():
    """Fetch a list of files stored on the gRPC server.

    This endpoint sends a request to the gRPC server to retrieve all available file names.
    Returns
    -------
    dict
        A JSON-serializable dictionary containing a list of file names with the key `filenames`.
        Example:
        {
            "filenames": ["file1.txt", "file2.png"]
        }
    """
    try:
        # # Send a request to the gRPC server and receive the response
        response = await grpc_stub.ListFiles(EmptyRequest())
        # Convert gRPC response to a JSON-serializable format
        return {"filenames": list(response.filenames)}
    except grpc.aio.AioRpcError as e:
        # Log the error for debugging
        print(f"RPC failed: {e.details()}")
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/upload/")
async def upload_file(file: UploadFile):
    """
    Endpoint to upload a file to the gRPC server.

    The file is read in chunks and streamed to the gRPC server for storage.

    Args:
        file (UploadFile): The file object sent in the request.

    Returns:
        dict: A success message from the gRPC server.

    Raises:
        HTTPException: If the gRPC server encounters an error during the upload.
    """
    try:
        async def file_chunk_generator():
            yield FileChunk(filename=file.filename)
            while chunk := await file.read(1024):
                yield FileChunk(content=chunk)

        response = await grpc_stub.UploadFile(file_chunk_generator())
        return {"message": response.message}
    
    except Exception as e:
        error_message = str(e)
        print("Error:", error_message)
        print("Traceback:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=error_message)

@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Endpoint to download a file from the gRPC server.

    The file is streamed from the gRPC server in chunks and returned as a response.

    Args:
        filename (str): The name of the file to download.

    Returns:
        StreamingResponse: A streamed response containing the file data.

    Raises:
        HTTPException: 
            - If the file is not found on the gRPC server.
            - If the gRPC server encounters any other error.
    """
    async def file_stream():
        request = FileRequest(filename=filename)
        try:
            async for chunk in grpc_stub.DownloadFile(request):
                yield chunk.content
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:
                raise HTTPException(status_code=404, detail=e.details())
            raise HTTPException(status_code=500, detail=f"gRPC error: {e.details()}")

    
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(file_stream(), media_type="application/octet-stream", headers=headers)
