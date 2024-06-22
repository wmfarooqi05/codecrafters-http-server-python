import socket

OK_RESP = b"HTTP/1.1 200 OK\r\n\r\n"
ERROR_RESP = b"HTTP/1.1 404 Not Found\r\n\r\n"


def get_content_header(string):
    return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(string)}\r\n\r\n{string}"


def parse_headers(data):
    headers = {}
    lines = data.split('\r\n')
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key] = value
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

        headers = parse_headers(request_data)

        data = request_data.split('\r\n')
        if not data:
            break

        path = data[0].split(' ')[1]

        if path == "/":
            connection.send(OK_RESP)
        elif path.startswith("/echo"):
            request_str = path.split("/echo/")[1]
            connection.sendall(get_content_header(request_str).encode())
        elif path.startswith("/user-agent"):
            user_agent = headers['User-Agent']
            connection.sendall(get_content_header(user_agent).encode())
        else:
            connection.send(ERROR_RESP)

        # Closing the connection
        connection.close()


if __name__ == "__main__":
    main()
