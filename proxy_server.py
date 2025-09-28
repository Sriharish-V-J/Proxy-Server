import socket
import threading
import select
from urllib.parse import urlparse

LISTEN_ADDR = '127.0.0.1'   
LISTEN_PORT = 8888          
BUFFER_SIZE = 4096          
SOCKET_TIMEOUT = 5          

# Parse the HTTP request to extract the host and port
def extract_host_port(request_bytes):
    text = request_bytes.decode('iso-8859-1', errors='replace')
    header_end = text.find('\r\n\r\n')
    headers_text = text if header_end == -1 else text[:header_end + 2]
    lines = headers_text.split('\r\n')
    if not lines:
        raise ValueError("Empty request")
    first_line = lines[0]                    
    parts = first_line.split()
    if len(parts) < 2:
        raise ValueError("Malformed request line")
    method = parts[0].upper()
    uri = parts[1]


    if method == 'CONNECT':
        if ':' in uri:
            host, port_str = uri.split(':', 1)
            return host, int(port_str), method, first_line, headers_text
        else:
            return uri, 443, method, first_line, headers_text

    parsed = urlparse(uri)
    if parsed.scheme and parsed.hostname:
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
        return parsed.hostname, port, method, first_line, headers_text

    for line in lines[1:]:
        if line.lower().startswith('host:'):
            host_header = line.split(':', 1)[1].strip()
            if ':' in host_header:
                h, p = host_header.split(':', 1)
                return h, int(p), method, first_line, headers_text
            return host_header, 80, method, first_line, headers_text

    raise ValueError("Host header not found and URI not absolute")

# Handle a client connection
def handle_client(client_sock, client_addr):

    client_sock.settimeout(SOCKET_TIMEOUT)
    try:
        
        request = b''
        while True:
            chunk = client_sock.recv(BUFFER_SIZE)
            if not chunk:
                return
            request += chunk
            if b'\r\n\r\n' in request:
                break

            if len(request) > 64 * 1024:
                break


        try:
            host, port, method, first_line, headers_text = extract_host_port(request)
        except ValueError as e:
            print(f"[{client_addr[0]}] Error parsing request: {e}")
            return

        print(f"[{client_addr[0]}] {first_line} -> {host}:{port}")


        if method == 'CONNECT':
            try:
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.settimeout(SOCKET_TIMEOUT)
                remote.connect((host, port))
            except Exception as e:
                print(f"[{client_addr[0]}] CONNECT connect error: {e}")
                client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                return

            client_sock.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")

            sockets = [client_sock, remote]
            try:
                while True:
                    rlist, _, _ = select.select(sockets, [], sockets, SOCKET_TIMEOUT)
                    if not rlist:
                        break
                    for s in rlist:
                        data = s.recv(BUFFER_SIZE)
                        if not data:
                            return
                        if s is client_sock:
                            remote.sendall(data)
                        else:
                            client_sock.sendall(data)
            finally:
                remote.close()
                return

        text = request.decode('iso-8859-1', errors='replace')
        print("Request: \n",text)
        lines = text.split('\r\n')
        first_line = lines[0]
        parts = first_line.split()
        if len(parts) >= 3:
            method, uri, version = parts[0], parts[1], parts[2]
            parsed = urlparse(uri)
            if parsed.scheme and parsed.hostname:
                path = parsed.path or '/'
                if parsed.query:
                    path += '?' + parsed.query
                lines[0] = f"{method} {path} {version}"
                request = '\r\n'.join(lines).encode('iso-8859-1')

        try:
            remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(SOCKET_TIMEOUT)
            remote.connect((host, port))
            remote.sendall(request)
        except Exception as e:
            print(f"[{client_addr[0]}] Remote connect/send error: {e}")
            client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            return

        try:
            while True:
                data = remote.recv(BUFFER_SIZE)
                if not data:
                    break
                print("Response: \n",data.decode('iso-8859-1', errors='replace'))
                client_sock.sendall(data)
        finally:
            remote.close()

    except socket.timeout:
        print(f"[{client_addr[0]}] Socket timeout")
    except Exception as e:
        print(f"[{client_addr[0]}] Unexpected error: {e}")
    finally:
        try:
            client_sock.close()
        except Exception:
            pass

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LISTEN_ADDR, LISTEN_PORT))
    server.listen(100)
    print(f"Proxy listening on {LISTEN_ADDR}:{LISTEN_PORT} (HTTP only; CONNECT -> tunnel)")

    try:
        while True:
            client_sock, client_addr = server.accept()
            print(f"Accepted {client_addr[0]}:{client_addr[1]}")
            t = threading.Thread(target=handle_client, args=(client_sock, client_addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("Shutting down proxy")
    finally:
        server.close()

if __name__ == '__main__':
    main()
