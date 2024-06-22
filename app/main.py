import os
import socket
import sys
import gzip
from typing import Dict, List, Set

OK_RESP = b"HTTP/1.1 200 OK\r\n\r\n"
ERROR_RESP = b"HTTP/1.1 404 Not Found\r\n\r\n"

SUPPORTED_ENCODINGS: List[str] = ["gzip"]


def get_valid_encoding(encodings: str) -> Set[str]:
    encodings_list = [item.strip() for item in encodings.split(',')]
    return set(encodings_list).intersection(SUPPORTED_ENCODINGS)


def get_content_header(data: str, headers: Dict[str, str]) -> bytes:
    """
    Constructs HTTP headers and body for the response.

    Args:
        data (str): The response body data.
        headers (Dict[str, str]): The request headers.

    Returns:
        bytes: The complete HTTP response.
    """
    body = data.encode()
    extra_headers = []
    encoding = headers.get("accept-encoding")

    if encoding and "gzip" in get_valid_encoding(encoding):
        body = gzip.compress(body)
        extra_headers.append(b"Content-Encoding: gzip\r\n")

    response = [
        b"HTTP/1.1 200 OK\r\n",
        *extra_headers,
        b"Content-Type: text/plain\r\n",
        b"Content-Length: %d\r\n" % len(body),
        b"\r\n",
        body,
    ]

    return b"".join(response)


def get_streaming_header(content: str) -> bytes:
    """
    Constructs headers for streaming content.

    Args:
        content (str): The content to stream.

    Returns:
        bytes: The complete HTTP response.
    """
    response = (
        f"HTTP/1.1 200 OK\r\n"
        f"Content-Type: application/octet-stream\r\n"
        f"Content-Length: {len(content)}\r\n\r\n"
        f"{content}"
    )
    return response.encode()


def create_directory(directory_path: str) -> None:
    """
    Creates a directory if it does not exist.

    Args:
        directory_path (str): Path to the directory.
    """
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")


def parse_headers(data: str) -> Dict[str, str]:
    """
    Parses HTTP headers from the request data.

    Args:
        data (str): The raw request data.

    Returns:
        Dict[str, str]: A dictionary of headers.
    """
    headers = {}
    lines = data.split('\r\n')
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key.lower()] = value
    return headers


def handle_get_request(path: str, headers: Dict[str, str], connection: socket.socket) -> None:
    """
    Handles GET requests.

    Args:
        path (str): The request path.
        headers (Dict[str, str]): The request headers.
        connection (socket.socket): The client connection socket.
    """
    if path == "/":
        connection.send(OK_RESP)
    elif path.startswith("/echo"):
        request_str = path.split("/echo/")[1]
        connection.sendall(get_content_header(request_str, headers))
    elif path.startswith("/user-agent"):
        user_agent = headers.get('user-agent', '')
        connection.sendall(get_content_header(user_agent, headers))
    elif path.startswith('/files/') and sys.argv[1] == '--directory':
        file_name = path.replace('/files/', '')
        file_path = os.path.join(sys.argv[2], file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                file_content = file.read()
                connection.send(get_streaming_header(file_content))
        else:
            connection.sendall(ERROR_RESP)
    else:
        connection.send(ERROR_RESP)


def handle_post_request(path: str, headers: Dict[str, str], body: str, connection: socket.socket) -> None:
    """
    Handles POST requests.

    Args:
        path (str): The request path.
        headers (Dict[str, str]): The request headers.
        body (str): The request body.
        connection (socket.socket): The client connection socket.
    """
    if path.startswith('/files/') and sys.argv[1] == '--directory':
        if headers.get('content-type') == "application/octet-stream" and headers.get('content-length'):
            file_name = path.replace('/files/', '')
            full_path = os.path.join(sys.argv[2], file_name)
            create_directory(os.path.dirname(full_path))
            with open(full_path, 'w') as file:
                file.write(body)
                connection.send(b'HTTP/1.1 201 Created\r\n\r\n')
        else:
            connection.send(ERROR_RESP)
    else:
        connection.send(ERROR_RESP)


def main() -> None:
    """
    The main function to start the server.
    """
    print("Logs from your program will appear here!")

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        connection, address = server_socket.accept()
        request_data = connection.recv(1024).decode("utf-8")

        if not request_data:
            connection.close()
            continue

        header_data, body = request_data.split('\r\n\r\n', 1)
        headers = parse_headers(header_data)

        request_line = header_data.split('\r\n')[0]
        request_method, path, _ = request_line.split(' ')

        if request_method.upper() == "GET":
            handle_get_request(path, headers, connection)
        elif request_method.upper() == "POST":
            handle_post_request(path, headers, body, connection)
        else:
            connection.send(ERROR_RESP)

        connection.close()


if __name__ == "__main__":
    main()
