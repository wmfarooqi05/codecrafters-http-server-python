import socket

OK_RESP = b"HTTP/1.1 200 OK\r\n\r\n"
ERROR_RESP = b"HTTP/1.1 404 Not Found\r\n\r\n"


def get_content_header(string):
    return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(string)}\r\n\r\n{string}"


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)

    while True:
        connection, address = server_socket.accept()
        data = connection.recv(1024).decode("utf-8").split('\r\n')

        if not data:
            break

        data = data[0].split(' ')[1]

        if data == "/":
            connection.send(OK_RESP)
        elif data.find("/echo") != -1:
            request_str = data.split("/echo/")[1]
            connection.sendall(get_content_header(request_str).encode())
        else:
            connection.send(ERROR_RESP)

        # Closing the connection
        connection.close()


if __name__ == "__main__":
    main()
