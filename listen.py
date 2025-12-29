import socket

HOST = '127.0.0.1'
PORT = 8888

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print(f"Listening on {HOST}:{PORT}")

client_socket, client_address = server.accept()
print("Client connected:", client_address)

data = client_socket.recv(4096)
print("---- RAW REQUEST ----")
print(data.decode(errors='replace'))
print("---------------------")

client_socket.close()
server.close()
