import json, sys, re
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
MARKETS=json.load(open(sys.argv[1]))
def iso(d): return d.strftime("%Y-%m-%dT%H:%M:%S.000Z")
class H(BaseHTTPRequestHandler):
    def send(self, o, code=200):
        b=json.dumps(o).encode(); self.send_response(code); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        now=datetime.now(timezone.utc); p=self.path
        if p.endswith("/markets"): return self.send({"markets":MARKETS})
        if p.endswith("/next"):
            offs={"JP":2*3600+14*60,"KR":3*3600,"US":-3600,"AU":5*3600,"DE":-12*3600,"IN":4*3600}
            return self.send({"now":iso(now),"markets":[{"market":m["code"],"slug":m["code"],"proAt":iso(now-timedelta(hours=3)),"freeAt":iso(now+timedelta(seconds=offs.get(m["code"],8*3600)))} for m in MARKETS]})
        m=re.search(r"/levels/([A-Z]+)",p)
        if m:
            code=m.group(1); rep={"slug":"daily-report-2026-10-13","title":"t","date":"2026-10-13","freeAt":iso(now+(timedelta(hours=-1) if code=="US" else timedelta(hours=2,minutes=14))),"proAt":iso(now-timedelta(hours=3)),"url":"https://littlebirdtrading.com/trade-plans/daily-report-2026-10-13"}
            if code!="US": return self.send({"market":code,"access":"locked","pro":False,"report":rep,"symbols":None})
            def L(v,l,k): return {"value":v,"label":l,"kind":k,"timeframe":"day"}
            sym={"SPY":{"signal":"tailwind","lines":[L(578.4,"R2","resistance"),L(574.1,"R1","resistance"),L(571.25,"Pivot","pivot"),L(568.6,"S1","support"),L(564.9,"S2","support")]},
                 "ES":{"signal":"tailwind","lines":[L(5821.5,"R1","resistance"),L(5790.25,"Pivot","pivot"),L(5761,"S1","support")]},
                 "QQQ":{"signal":"perch","lines":[L(498.2,"R1","resistance"),L(492.8,"S1","support")]},
                 "NQ":{"signal":"headwind","lines":[L(20510,"R1","resistance"),L(20302.5,"S1","support")]}}
            return self.send({"market":code,"access":"free","pro":False,"report":rep,"symbols":sym})
        self.send({"error":"nope"},404)
    def do_POST(self):
        n=int(self.headers.get('content-length',0)); b=self.rfile.read(n).decode()
        open('posts.log','a').write(self.path+' '+b+'\n'); self.send({"ok":True})
    def log_message(self,*a): pass
HTTPServer(("127.0.0.1",8787),H).serve_forever()
