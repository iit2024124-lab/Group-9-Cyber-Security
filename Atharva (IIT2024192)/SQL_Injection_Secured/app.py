"""Local classroom lab. Standard library only; no external services."""
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parent / 'static'
PORT = 8002


def authenticate(username, password):
    with sqlite3.connect(':memory:') as db:
        db.row_factory = sqlite3.Row
        db.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, name TEXT, email TEXT)')
        db.executemany('INSERT INTO users VALUES (?, ?, ?, ?, ?)', [
            (1, 'alex', 'Maison!26', 'Alex Morgan', 'alex@example.com'),
            (2, 'taylor', 'CozyHome!26', 'Taylor Reed', 'taylor@example.com')])
        try:

            row = db.execute("SELECT id, username, name, email FROM users WHERE username = ? AND password = ?", (username, password)).fetchone()
        except sqlite3.Error:
            row = None
        return dict(ok=bool(row), user=dict(row) if row else None,
                    message='Welcome back.' if row else 'Incorrect username or password.')


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data, content_type='application/json'):
        payload = json.dumps(data).encode() if content_type == 'application/json' else data
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        route = urlsplit(self.path).path
        files = {'/': ('index.html', 'text/html; charset=utf-8'),
                 '/style.css': ('style.css', 'text/css; charset=utf-8'),
                 '/app.js': ('app.js', 'text/javascript; charset=utf-8')}
        if route not in files:
            return self.reply(404, {'error': 'Not found'})
        name, mime = files[route]
        self.reply(200, (ROOT / name).read_bytes(), mime)

    def do_POST(self):
        if self.path != '/api/login':
            return self.reply(404, {'error': 'Not found'})
        if self.headers.get('Origin') not in (None, f'http://127.0.0.1:{PORT}', f'http://localhost:{PORT}'):
            return self.reply(403, {'error': 'Foreign origin rejected'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4096:
                raise ValueError()
            body = json.loads(self.rfile.read(size))
            username, password = body['username'], body['password']
            if not all(isinstance(x, str) and len(x) <= 256 for x in (username, password)):
                raise ValueError()
        except (ValueError, KeyError, TypeError):
            return self.reply(400, {'error': 'Invalid request'})
        result = authenticate(username, password)
        self.reply(200, result)


if __name__ == '__main__':
    print(f'Maison running at http://127.0.0.1:{PORT} (Ctrl+C to stop)', flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
