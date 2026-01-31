
import http.client
import json
import time

HOST = "127.0.0.1"
PORT = 8000
PAYLOAD = json.dumps({"message": "qual o clima para hoje em artur nogueira"})
HEADERS = {
    "X-API-Key": "ziva-terminal-chat-key",
    "Content-Type": "application/json",
    "Connection": "close"
}

print(f"Testing connection to http://{HOST}:{PORT}/chat using http.client...")
start = time.time()
try:
    conn = http.client.HTTPConnection(HOST, PORT, timeout=10)
    conn.request("POST", "/chat", PAYLOAD, HEADERS)
    response = conn.getresponse()
    data = response.read().decode()
    print(f"Status Code: {response.status}")
    print(f"Response: {data[:200]}")
    print(f"Time taken: {time.time() - start:.2f}s")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
    print(f"Time taken: {time.time() - start:.2f}s")
