from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import json
from db import init_db
from services import (
    dashboard_data, list_cases, list_inventory, list_replenishments,
    list_notifications, list_audit, create_case, run_replenishment,
    decide_replenishment
)
HOST, PORT = "127.0.0.1", 8000

class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        body=json.dumps(data, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(body)))
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        self.wfile.write(body)
    def send_html(self, body):
        b=body.encode()
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length",str(len(b)))
        self.end_headers()
        self.wfile.write(b)
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Headers","Content-Type")
        self.send_header("Access-Control-Allow-Methods","GET, POST, OPTIONS")
        self.end_headers()
    def do_GET(self):
        p=urlparse(self.path).path
        if p=="/":
            self.send_html(open("static/index.html",encoding="utf-8").read()); return
        routes={
            "/api/health":lambda:{"status":"ok","service":"RetailOps Automation Hub v2"},
            "/api/dashboard":dashboard_data,
            "/api/cases":lambda:{"cases":list_cases()},
            "/api/inventory":lambda:{"inventory":list_inventory()},
            "/api/replenishments":lambda:{"replenishments":list_replenishments()},
            "/api/notifications":lambda:{"notifications":list_notifications()},
            "/api/audit":lambda:{"audit":list_audit()},
        }
        if p in routes:
            self.send_json(routes[p]()); return
        self.send_json({"error":"Not found"},404)
    def do_POST(self):
        p=urlparse(self.path).path
        try:
            data=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0)) or 0) or b"{}")
        except Exception:
            self.send_json({"error":"Invalid JSON"},400); return
        try:
            if p=="/api/cases":
                self.send_json(create_case(data),201); return
            if p=="/api/pos/reconcile":
                data.setdefault("category","POS discrepancy")
                self.send_json(create_case(data),201); return
            if p=="/api/automation/replenishment":
                self.send_json(run_replenishment()); return
            if p.startswith("/api/replenishments/") and p.endswith("/decision"):
                rid=p.split("/")[-2]
                self.send_json(decide_replenishment(int(rid),data),200); return
        except ValueError as e:
            self.send_json({"error":str(e)},400); return
        except LookupError as e:
            self.send_json({"error":str(e)},404); return
        self.send_json({"error":"Not found"},404)
    def log_message(self,*args): pass

if __name__=="__main__":
    init_db()
    print(f"RetailOps Automation Hub v2 running at http://localhost:{PORT}")
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
