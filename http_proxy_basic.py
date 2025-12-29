import socket
from urllib.parse import urlparse

LISTEN_HOST = '127.0.0.1'
LISTEN_PORT = 8888
BUFFER_SIZE = 4096

# 1. Create listening socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((LISTEN_HOST, LISTEN_PORT))
server.listen(1)

print(f"Proxy listening on {LISTEN_HOST}:{LISTEN_PORT}")

# 2. Accept one client connection
client_socket, client_addr = server.accept()
print("Client connected:", client_addr)

# 3. Receive HTTP request
request = client_socket.recv(BUFFER_SIZE)
request_text = request.decode(errors='replace')
print("---- REQUEST ----")
print(request_text)

# 4. Parse request line
lines = request_text.split('\r\n')
request_line = lines[0]
method, url, version = request_line.split()

parsed_url = urlparse(url)
host = parsed_url.hostname
port = parsed_url.port or 80
path = parsed_url.path or '/'

# 5. Rewrite request line (absolute → relative)
lines[0] = f"{method} {path} {version}"
new_request = '\r\n'.join(lines).encode()

# 6. Connect to destination server
remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
remote_socket.connect((host, port))

# 7. Forward modified request
remote_socket.sendall(new_request)

# 8. Relay response back to browser
while True:
    data = remote_socket.recv(BUFFER_SIZE)
    if not data:
        break
    client_socket.sendall(data)

# 9. Cleanup
remote_socket.close()
client_socket.close()
server.close()
