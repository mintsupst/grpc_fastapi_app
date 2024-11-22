import os
import asyncio
import grpc
from concurrent import futures
from file_transfer_pb2 import FileChunk, UploadResponse, FileListResponse, EmptyRequest
from file_transfer_pb2_grpc import FileServiceServicer, add_FileServiceServicer_to_server


class FileService(FileServiceServicer):
    """ Class for handling file operations over gRPC.

    Attributes
    ----------
    directory:
        ="files" defines a directory for uploaded files

    filenames:
        list of all the uploaded files
    Methods
    -------
    UploadFile(request_iterator, context):
        Asynchronously receives a file in chunks from the client

        and stores it on the server. 

    DownloadFile(request, context):
        Streams a file in chunks from the server's storage back to the client.
    """
    def __init__(self):
        """ Defines attributes and ensures path to uploaded files exists"""

        self.directory = "files"
        os.makedirs(self.directory, exist_ok=True) # Ensure directory exists


    async def ListFiles(self, request: EmptyRequest, context):
        """List all files stored on the server.

        Parameters
        ----------
        request : EmptyRequest
            An empty request message.
        context : grpc.ServicerContext
            Provides RPC-specific information and utilities for error handling.
        """
        try:
            self.filenames = os.listdir(self.directory) # update filenames attribute
            return FileListResponse(filenames=self.filenames) 
        
        except Exception as e:  #exception handling
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return FileListResponse(filenames=[])


    async def UploadFile(self, request_iterator, context):
        """ Receives file from the client and stores it on the server

        (Inside docker container). 

        **I tried to bind project folder to folder inside the container but it didn't work**

        Parameters
        ----------
            request_iterator : iterable

            An iterator of file chunks streamed by the client.
                
            context : grpc.ServicerContext

            Provides RPC-specific information and utilities for error handling.
        """ 
        try:
            
            # Open file in append binary mode
            filename = None
            async for chunk in request_iterator:
                if filename is None:
                # Retrieve filename from the first chunk
                    filename = chunk.filename
                    if not filename:
                        raise ValueError("Filename is missing in the request")

                # Write the file content
                with open(f"files/{filename}", "ab") as f:
                    f.write(chunk.content)
            return UploadResponse(message="File upload succesfull")
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return UploadResponse(message="File upload failed")

    async def DownloadFile(self, request, context):
        """ Streams file from the server to client in chunks

        Parameters
        ----------
        request : DownloadRequest

            Contains the name of the file to be downloaded.

        context : grpc.ServicerContext

            Provides RPC-specific information and utilities for error handling.

        Yields
        ------

        FileChunk
            Chunks of the requested file.

        Raises
        ------
        grpc.RpcError

            If the requested file does not exist or an internal error occurs.
        """
        filename = f"files/{request.filename}"
        try:
            with open(filename, "rb") as f:
                while chunk := f.read(1024):  # Read file in 1KB chunks
                    yield FileChunk(content=chunk)
        except FileNotFoundError:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details(f"File '{request.filename}' not found.")
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))

async def serve():
    """ Starts server and listens for connections """
    # Creates grpc server instance
    server = grpc.aio.server()
    
    # Adds servicer class to that server
    add_FileServiceServicer_to_server(FileService(), server)

    # Creates port for connection
    server.add_insecure_port("[::]:50051")

    # Self explanatory
    await server.start()
    print("gRPC server started on port 50051")
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
