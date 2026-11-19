#!/usr/bin/env python3
"""Small, dependency-free backend for Forsyth Connect.

Run from the project root:
    python3 backend/server.py

The server exposes the resource directory as JSON and accepts community
corrections without requiring a database or third-party packages.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_PATH = PROJECT_ROOT / "frontend" / "index.html"
DATA_PATH = PROJECT_ROOT / "data" / "resources.json"
DATA_DIRECTORY = Path(
    os.environ.get("FORSYTH_DATA_DIR")
    or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
    or PROJECT_ROOT / "data"
).expanduser()
DATABASE_PATH = DATA_DIRECTORY / "forsyth_connect.sqlite3"
MAX_BODY_BYTES = 20_000
DATA_LOCK = threading.RLock()
FRONTEND_LOCK = threading.RLock()
DATA_CACHE: dict | None = None
DATA_CACHE_MTIME_NS: int | None = None
FRONTEND_CACHE: bytes | None = None
FRONTEND_CACHE_MTIME_NS: int | None = None


def load_data() -> dict:
    global DATA_CACHE, DATA_CACHE_MTIME_NS
    current_mtime = DATA_PATH.stat().st_mtime_ns
    with DATA_LOCK:
        if DATA_CACHE is None or DATA_CACHE_MTIME_NS != current_mtime:
            with DATA_PATH.open("r", encoding="utf-8") as handle:
                DATA_CACHE = json.load(handle)
            DATA_CACHE_MTIME_NS = current_mtime
        return DATA_CACHE


def load_frontend() -> bytes:
    global FRONTEND_CACHE, FRONTEND_CACHE_MTIME_NS
    current_mtime = FRONTEND_PATH.stat().st_mtime_ns
    with FRONTEND_LOCK:
        if FRONTEND_CACHE is None or FRONTEND_CACHE_MTIME_NS != current_mtime:
            FRONTEND_CACHE = FRONTEND_PATH.read_bytes()
            FRONTEND_CACHE_MTIME_NS = current_mtime
        return FRONTEND_CACHE


def initialize_database() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH, timeout=5) as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=5000")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at TEXT NOT NULL,
                resource_name TEXT NOT NULL,
                message TEXT NOT NULL,
                contact TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.commit()


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def matches_query(resource: dict, query: str, lang: str) -> bool:
    if not query:
        return True
    description = resource.get("desc", {}).get(lang, resource.get("desc", {}).get("en", ""))
    haystack = normalized(" ".join([
        resource.get("name", ""),
        resource.get("category", ""),
        resource.get("address", ""),
        description,
    ]))
    return all(term in haystack for term in normalized(query).split())


def filtered_payload(category: str = "", query: str = "", lang: str = "en") -> dict:
    # Never mutate DATA_CACHE: a filtered request must not change what later
    # users receive from an unfiltered request.
    source = load_data()
    resources = [
        resource for resource in source.get("resources", [])
        if (not category or category == "All" or resource.get("category") == category)
        and matches_query(resource, query, lang)
    ]
    payload = {**source, "resources": resources}
    payload["server"] = {
        "source": "Forsyth Connect Python backend",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    return payload


def json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class AppHandler(BaseHTTPRequestHandler):
    server_version = "ForsythConnect/1.0"
    protocol_version = "HTTP/1.1"

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(self.server.client_timeout)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # Keep the terminal useful while still showing requests.
        print(f"{self.address_string()} - {format % args}")

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, body: bytes, content_type: str) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/api/health":
            self.send_json({
                "ok": True,
                "service": "Forsyth Connect",
                "backend": "python-standard-library",
                "maxWorkers": self.server.max_workers,
                "requestQueue": self.server.request_queue_size,
            })
            return

        if parsed.path == "/api/resources":
            category = query.get("category", [""])[0]
            search_values = query.get("q") or query.get("query") or [""]
            search = search_values[0]
            lang = query.get("lang", ["en"])[0]
            if lang not in {"en", "es"}:
                lang = "en"
            self.send_json(filtered_payload(category, search, lang))
            return

        if parsed.path in {"/", "/index.html"}:
            if not FRONTEND_PATH.exists():
                self.send_error(HTTPStatus.NOT_FOUND, "Frontend file not found")
                return
            self.send_text(load_frontend(), "text/html; charset=utf-8")
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/feedback":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_BODY_BYTES:
                raise ValueError("Request is too large")
            body = json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return

        resource_name = str(body.get("resourceName", "")).strip()
        message = str(body.get("message", "")).strip()
        contact = str(body.get("contact", "")).strip()
        names = {resource["name"] for resource in load_data().get("resources", [])}

        if resource_name not in names:
            self.send_json({"error": "Choose a listed resource."}, HTTPStatus.BAD_REQUEST)
            return
        if not message or len(message) < 8:
            self.send_json({"error": "Please describe the update in at least 8 characters."}, HTTPStatus.BAD_REQUEST)
            return
        if len(message) > 2_000 or len(contact) > 200:
            self.send_json({"error": "One of the fields is too long."}, HTTPStatus.BAD_REQUEST)
            return
        if contact and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", contact):
            self.send_json({"error": "Enter a valid email or leave contact blank."}, HTTPStatus.BAD_REQUEST)
            return

        with sqlite3.connect(DATABASE_PATH, timeout=5) as connection:
            connection.execute("PRAGMA busy_timeout=5000")
            connection.execute(
                "INSERT INTO feedback (received_at, resource_name, message, contact) VALUES (?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), resource_name, message, contact),
            )
            connection.commit()

        self.send_json({"ok": True, "message": "Thanks — your update was received."}, HTTPStatus.CREATED)


class ScalableHTTPServer(HTTPServer):
    """Bounded worker pool plus a larger accept queue for concurrent users."""

    allow_reuse_address = True
    request_queue_size = 512

    def __init__(self, server_address, handler_class, max_workers: int, client_timeout: int):
        # HTTPServer may call server_close() if binding fails. Initialize the
        # executor slot first so that startup errors remain readable.
        self._executor: ThreadPoolExecutor | None = None
        super().__init__(server_address, handler_class)
        self.max_workers = max_workers
        self.client_timeout = client_timeout
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="forsyth-connect",
        )

    def process_request(self, request, client_address) -> None:
        assert self._executor is not None
        self._executor.submit(self._process_request, request, client_address)

    def _process_request(self, request, client_address) -> None:
        try:
            self.finish_request(request, client_address)
            self.shutdown_request(request)
        except Exception:
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def server_close(self) -> None:
        super().server_close()
        if self._executor is not None:
            self._executor.shutdown(wait=True, cancel_futures=True)
            self._executor = None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Forsyth Connect backend")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--workers", type=int, default=128, help="Maximum concurrent request handlers")
    parser.add_argument("--timeout", type=int, default=15, help="Idle client connection timeout in seconds")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be at least 1")
    if args.timeout < 1:
        parser.error("--timeout must be at least 1")
    initialize_database()
    server = ScalableHTTPServer((args.host, args.port), AppHandler, args.workers, args.timeout)
    print(f"Forsyth Connect running at http://{args.host}:{args.port}")
    print(f"Capacity: {args.workers} concurrent request handlers; queue: {server.request_queue_size}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
