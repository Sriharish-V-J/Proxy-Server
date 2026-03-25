# HTTP Proxy Server

A simple HTTP proxy server implemented using Python sockets. This project demonstrates how HTTP requests can be intercepted, modified, and forwarded between a client and a destination server.

---

## 🚀 Features

- Intercepts HTTP requests from client (browser)
- Parses HTTP request line (method, URL, version)
- Extracts destination host and port
- Rewrites request from absolute URL → relative path
- Forwards request to target server
- Relays server response back to client
- Displays raw HTTP traffic for analysis

---

## 🧠 How It Works

1. The proxy listens for incoming client connections.
2. When a client connects, it receives the HTTP request.
3. The request is parsed to extract:
   - Method (GET, POST, etc.)
   - URL
   - HTTP version
4. The absolute URL is converted into a relative path.
5. A new socket connection is established with the destination server.
6. The modified request is forwarded.
7. The response from the server is relayed back to the client.

---

## 🛠️ Tech Stack

- Python
- Socket Programming
- HTTP Protocol (Basic)

---

## ▶️ Usage

### 1. Run the proxy server

```bash
python proxy.py
