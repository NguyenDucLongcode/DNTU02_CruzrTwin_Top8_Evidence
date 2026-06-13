"""
CruzrTwin ASEAN — Minimal Web Dashboard Server
Serves the dashboard HTML and provides a /api/trace JSON endpoint
that reads all JSONL log files for live trace display.
"""

import os
import sys
import json
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.common.config import get_config

# Use standard library http.server to avoid Flask dependency
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import threading

DASHBOARD_DIR = os.path.dirname(os.path.abspath(__file__))


def load_jsonl(path: str) -> list:
    """Load a JSONL file and return a list of dicts."""
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def build_trace_response() -> dict:
    """Build the trace response from all log files."""
    cfg = get_config()
    log_dir = cfg["log_dir"]

    return {
        "demo_run_id": cfg["demo_run_id"],
        "sensor_readings": load_jsonl(os.path.join(log_dir, "sensor_readings.jsonl")),
        "ai_detections": load_jsonl(os.path.join(log_dir, "ai_detection.jsonl")),
        "alert_events": load_jsonl(os.path.join(log_dir, "alert_events.jsonl")),
        "robot_actions": load_jsonl(os.path.join(log_dir, "robot_actions.jsonl")),
        "operator_ack": load_jsonl(os.path.join(log_dir, "operator_ack.jsonl")),
        "orion_state": load_jsonl(os.path.join(log_dir, "orion_state.jsonl")),
    }


class DashboardHandler(SimpleHTTPRequestHandler):
    """Custom handler that serves index.html and the trace API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/trace":
            self._serve_trace_api()
        elif parsed.path == "/" or parsed.path == "/index.html":
            self._serve_file("index.html", "text/html")
        else:
            super().do_GET()

    def _serve_trace_api(self):
        """Serve the trace JSON endpoint."""
        try:
            data = build_trace_response()
            body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            error_body = json.dumps({"error": str(e)}).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error_body)))
            self.end_headers()
            self.wfile.write(error_body)

    def _serve_file(self, filename, content_type):
        """Serve a static file from the dashboard directory."""
        filepath = os.path.join(DASHBOARD_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Override to use cleaner log format."""
        print(f"[Dashboard] {args[0]}")


def main():
    port = int(os.getenv("DASHBOARD_PORT", "8080"))

    # Change to project root so log_dir paths resolve correctly
    os.chdir(ROOT_DIR)

    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"\n{'='*55}")
    print(f"  CruzrTwin ASEAN Dashboard")
    print(f"{'='*55}")
    print(f"  URL:       http://localhost:{port}/")
    print(f"  Trace API: http://localhost:{port}/api/trace")
    print(f"  Log Dir:   {get_config()['log_dir']}")
    print(f"{'='*55}")
    print(f"  Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Dashboard] Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
