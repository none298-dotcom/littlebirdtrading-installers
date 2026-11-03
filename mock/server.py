"""Loopback-only installer fixture. Synthetic data, no production calls or credentials."""
import io
import json
import re
import sys
import zipfile
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


def export_file(path, now=NOW):
    """Synthetic Pine, JSON and Excel files for the export check (EXPORT-01). Returns (bytes, type, name) or None."""
    match = re.fullmatch(r"/api/app/export/(US|AT)/(pine|json|xlsx)", urlsplit(path).path)
    if not match:
        return None
    code, fmt = match.groups()
    name = "little-bird-trading-%s-fixture.%s" % ("index-levels" if code == "US" else "active-traders", fmt)
    rows = [("SPY", "resistance", "R1", 580.0), ("SPY", "pivot", "Pivot", 570.0), ("SPY", "support", "S1", 560.0)]
    if fmt == "pine":
        text = ('//@version=6\nindicator("Little Bird Trading fixture: LittleBirdTrading.com", shorttitle="LBT Levels: LittleBirdTrading.com", overlay=true)\n'
                'var table lbt = table.new(position.bottom_right, 1, 1)\n')
        return text.encode(), "text/plain", name
    if fmt == "json":
        body = {"schema_version": 1, "plan": "fixture", "symbols": {"SPY": [{"label": r[2], "kind": r[1], "level": r[3]} for r in rows]}}
        return json.dumps(body).encode(), "application/json", name
    sheet = "".join('<row r="%d"><c t="inlineStr"><is><t>%s</t></is></c><c><v>%s</v></c></row>' % (i + 1, r[2], r[3]) for i, r in enumerate(rows))
    parts = {
        "[Content_Types].xml": '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Levels" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": '<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>%s</sheetData></worksheet>' % sheet,
    }
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for key, value in parts.items():
            z.writestr(key, value)
    return out.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", name


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
            export = export_file(self.path)
            if export:
                data, kind, name = export
                self.send_response(200)
                self.send_header("Content-Type", kind)
                self.send_header("Content-Disposition", 'attachment; filename="%s"' % name)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
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
