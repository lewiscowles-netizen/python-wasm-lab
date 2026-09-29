#!/usr/bin/env python3
"""Serve the local service tutorial; see ../reference/external-service.md."""
import argparse
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


class ServiceHandler(BaseHTTPRequestHandler):
    def log_request(self, code="-", size="-"):
        self.log_message('"%s" %s %s request_id=%s', self.requestline, code, size, getattr(self, "request_id", "-"))

    def reply(self, status, payload=None):
        body = b"" if payload is None else json.dumps(payload).encode("utf-8")
        self.request_id = uuid.uuid4().hex
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Vary", "Origin")
        self.send_header("X-Request-ID", self.request_id)
        if self.headers.get("Origin") == self.server.allow_origin:
            self.send_header("Access-Control-Allow-Origin", self.server.allow_origin)
            self.send_header("Access-Control-Expose-Headers", "X-Request-ID")
            if self.command == "OPTIONS":
                self.send_header("Access-Control-Allow-Methods", "GET, POST")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
        try:
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def allowed(self):
        origin = self.headers.get("Origin")
        if origin is not None and origin != self.server.allow_origin:
            self.reply(403, {"error": "origin_not_allowed"})
            return False
        return True

    def do_OPTIONS(self):
        if not self.allowed():
            return
        method = self.headers.get("Access-Control-Request-Method")
        headers = {
            header.strip().lower()
            for header in self.headers.get("Access-Control-Request-Headers", "").split(",")
            if header.strip()
        }
        if method not in {"GET", "POST"} or not headers <= {"content-type"}:
            self.reply(403, {"error": "preflight_not_allowed"})
            return
        self.reply(204)

    def do_GET(self):
        if not self.allowed():
            return
        path = urlsplit(self.path).path
        if path == "/health":
            self.reply(200, {"ok": True})
        elif path == "/stock/widget":
            self.reply(200, {"sku": "widget", "available": 7, "unit_price_cents": 125})
        elif path == "/slow":
            time.sleep(2)
            self.reply(200, {"ok": True})
        else:
            self.reply(404, {"error": "not_found"})

    def do_POST(self):
        if not self.allowed():
            return
        if urlsplit(self.path).path != "/quote":
            self.reply(404, {"error": "not_found"})
            return
        if self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
            self.reply(415, {"error": "json_required"})
            return
        if self.headers.get("Transfer-Encoding"):
            self.reply(400, {"error": "content_length_required"})
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.reply(400, {"error": "content_length_required"})
            return
        if not 0 < length <= 4096:
            self.reply(413, {"error": "body_size"})
            return
        try:
            data = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            self.reply(400, {"error": "invalid_json"})
            return
        if not isinstance(data, dict) or data.get("sku") != "widget" or type(data.get("quantity")) is not int or not 1 <= data["quantity"] <= 7:
            self.reply(422, {"error": "invalid_quote", "quantity_range": [1, 7]})
            return
        self.reply(200, {"sku": "widget", "quantity": data["quantity"], "total_cents": 125 * data["quantity"]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8132)
    parser.add_argument("--allow-origin", default="http://127.0.0.1:8129")
    args = parser.parse_args()
    origin = urlsplit(args.allow_origin)
    if origin.scheme not in {"http", "https"} or not origin.netloc or origin.path or origin.query or origin.fragment or origin.username or origin.password:
        parser.error("--allow-origin must be a single HTTP(S) origin without a trailing slash")
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), ServiceHandler)
    except OSError as error:
        parser.error(str(error))
    server.allow_origin = args.allow_origin
    print("External service: http://127.0.0.1:%d (allows %s)" % (server.server_port, server.allow_origin), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
