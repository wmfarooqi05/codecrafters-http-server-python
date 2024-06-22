import os.path
import socket
import sys

OK_RESP = b"HTTP/1.1 200 OK\r\n\r\n"
ERROR_RESP = b"HTTP/1.1 404 Not Found\r\n\r\n"

SUPPORTED_ENCODINGS = ["gzip"]


def get_content_header(string, content_type="text/plain", encoding=""):
    resp = "HTTP/1.1 200 OK\r\n"
    resp += f"Content-Type: {content_type}\r\n"
    if encoding is not None and len(encoding) != 0 and encoding in SUPPORTED_ENCODINGS:
        resp += f"Content-Encoding: {encoding}\r\n"

    resp += f"Content-Length: {len(string)}\r\n\r\n{string}"
    return resp.encode()


def get_streaming_header(string):
    return (
        f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(string)}\r\n\r\n{string}"
        .encode()
    )


def create_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")


def parse_headers(data):
    headers = {}
    lines = data.split('\r\n')
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[f"{key}".lower()] = value
    return headers


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        connection, address = server_socket.accept()
        request_data = connection.recv(1024).decode("utf-8")

        header_data, body = request_data.split('\r\n\r\n', 1)
        headers = parse_headers(header_data)

        data = request_data.split('\r\n')
        if not data:
            break

        request_method = data[0].split(' ')[0]
        path = data[0].split(' ')[1]

        if request_method.upper() == "GET":
            if path == "/":
                connection.send(OK_RESP)
            elif path.startswith("/echo"):
                request_str = path.split("/echo/")[1]
                connection.sendall(
                    get_content_header(
                        request_str,
                        headers.get('content-type', 'text/plain'),
                        headers.get('accept-encoding', None)
                    )
                )

            elif path.startswith("/user-agent"):
                user_agent = headers['user-agent']
                connection.sendall(get_content_header(user_agent))
            elif path.startswith('/files/') and sys.argv[1] == '--directory':
                file_name = path.replace('/files/', '')
                file_path = os.path.join(sys.argv[2], file_name)
                if os.path.exists(file_path):
                    with open(file_path, 'r') as file:
                        file_content = file.read()
                        connection.send(get_streaming_header(file_content))
                else:
                    connection.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
            else:
                connection.send(ERROR_RESP)
        elif request_method.upper() == "POST":
            if path.startswith('/files/') and \
                    sys.argv[1] == '--directory' and \
                    headers['content-type'] == "application/octet-stream" and \
                    headers['content-length'] is not None:
                file_name = path.replace('/files/', '')
                full_path = os.path.join(sys.argv[2], file_name)
                create_directory("".join(full_path.split('/')[:-1]))

                with open(full_path, 'w') as file:
                    file.write(body)
                    connection.send(b'HTTP/1.1 201 Created\r\n\r\n')

        else:
            connection.send(ERROR_RESP)
        # Closing the connection
        connection.close()


if __name__ == "__main__":
    main()
