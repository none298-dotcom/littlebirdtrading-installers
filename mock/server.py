"""Loopback-only installer fixture. Synthetic data, no production calls or credentials."""
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit

NOW = datetime.now(timezone.utc)


def iso(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def payload(path, markets, now=NOW):
    path = urlsplit(path).path
    if path == "/api/app/markets":
        return {"markets": markets}, 200
    if path == "/api/app/next":
        return {"now": iso(now), "markets": [
            {"market": m["code"], "slug": "fixture-" + m["code"].lower(),
             "proAt": iso(now - timedelta(hours=3)),
             "freeAt": iso(now + timedelta(seconds=-3600 if m["code"] == "US" else 8040))}
            for m in markets]}, 200
    match = re.fullmatch(r"/api/app/levels/([A-Z]+)", path)
    if match:
        code = match.group(1)
        market = next((m for m in markets if m["code"] == code), None)
        if market is None:
            return {"error": "Unknown fixture list"}, 404
        report = {"slug": "fixture-" + code.lower(), "title": "Synthetic installer test",
                  "date": now.date().isoformat(), "proAt": iso(now - timedelta(hours=3)),
                  "freeAt": iso(now + timedelta(seconds=-3600 if code == "US" else 8040)),
                  "url": "http://127.0.0.1:8787/fixture/" + code.lower()}
        result = {"market": code, "access": "free" if code == "US" else "locked",
                  "pro": False, "report": report}
        if code == "US":
            result["symbols"] = {
                symbol.upper(): {"signal": "perch", "lines": [
                    {"value": base + delta, "label": label, "kind": kind, "timeframe": "day"}
                    for delta, label, kind in ((10, "R1", "resistance"), (0, "Pivot", "pivot"), (-10, "S1", "support"))]}
                for symbol, base in zip(market["symbols"], (570, 5800, 490, 20300))}
        return result, 200
    if path == "/api/app/me":
        return {"error": "Synthetic fixture is signed out"}, 401
    if path == "/api/app/sync":
        return {"error": "Sync requires Pro"}, 403
    return {"error": "Unknown fixture route"}, 404


def handler(markets):
    class Handler(BaseHTTPRequestHandler):
        def send(self, body, code=200):
            data = json.dumps(body).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            body, code = payload(self.path, markets)
            self.send(body, code)

        def do_POST(self):
            # Consume synthetic registrations without saving payloads or sending anything.
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            self.send({"ok": True})

        def log_message(self, *args):
            pass
    return Handler


if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as source:
        markets = json.load(source)
    if [m["code"] for m in markets] != ["US", "AT"]:
        raise ValueError("Installer fixture must contain US and AT only")
    HTTPServer(("127.0.0.1", 8787), handler(markets)).serve_forever()
