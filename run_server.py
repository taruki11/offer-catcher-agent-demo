from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "0.0.0.0"
PORT = 8501


class CacheFreeHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    import os

    os.chdir(root)
    server = ThreadingHTTPServer((HOST, PORT), CacheFreeHandler)
    print(f"Offer Catcher demo is running at http://{HOST}:{PORT}")
    print(f"Serving files from {root}")
    server.serve_forever()
