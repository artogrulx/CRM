import json
import mimetypes
import os
import socket
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 10101
DATA_FILE = "data.json"

class JSONServer(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def send_file(self, path, content_type=None):
        if not os.path.exists(path) or not os.path.isfile(path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
            return
        self.send_response(200)
        self.send_header('Content-Type', content_type or mimetypes.guess_type(path)[0] or 'application/octet-stream')
        self.end_headers()
        with open(path, 'rb') as f:
            self.wfile.write(f.read())

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_HEAD(self):
        request_path = self.path.split('?', 1)[0]
        if request_path in ('/', '/index.html'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            return
        if request_path == '/get-data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            return
        if request_path == '/data.json':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            return

        safe_path = os.path.normpath(request_path.lstrip('/'))
        if safe_path and os.path.isfile(safe_path) and not safe_path.startswith('..'):
            self.send_response(200)
            self.send_header('Content-Type', mimetypes.guess_type(safe_path)[0] or 'application/octet-stream')
            self.end_headers()
            return

        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        request_path = self.path.split('?', 1)[0]
        if request_path in ('/', '/index.html'):
            return self.send_file('index.html', 'text/html')
        if request_path == '/get-data':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            with open(DATA_FILE, 'r') as f:
                self.wfile.write(f.read().encode('utf-8'))
            return
        if request_path == '/data.json':
            return self.send_file(DATA_FILE, 'application/json')

        safe_path = os.path.normpath(request_path.lstrip('/'))
        if safe_path and os.path.isfile(safe_path) and not safe_path.startswith('..'):
            return self.send_file(safe_path)

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b'404 Not Found')

    def do_POST(self):
        if self.path == "/save-data":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            with open(DATA_FILE, 'w') as f:
                f.write(post_data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))

def ensure_data_file():
    if not os.path.exists(DATA_FILE):
        initial = {"users": {"ilkin": {"contacts": [], "orders": []}, "adin": {"contacts": [], "orders": []}}}
        with open(DATA_FILE, 'w') as f:
            json.dump(initial, f, indent=2)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return 'localhost'


if __name__ == "__main__":
    ensure_data_file()
    local_ip = get_local_ip()
    print(f"Backend Server running on 0.0.0.0:{PORT}")
    print(f"Access it from another machine at http://{local_ip}:{PORT}")
    ThreadingHTTPServer(('0.0.0.0', PORT), JSONServer).serve_forever()
