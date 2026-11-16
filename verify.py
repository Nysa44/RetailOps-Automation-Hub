"""Clean-database integration test. Run: python verify.py"""
import threading, urllib.request, json
from pathlib import Path
from db import DB_PATH, init_db
from app import Handler, ThreadingHTTPServer

if DB_PATH.exists(): DB_PATH.unlink()
init_db()
server=ThreadingHTTPServer(("127.0.0.1",8000),Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
def get(path):
    with urllib.request.urlopen("http://127.0.0.1:8000"+path,timeout=4) as r:return r.status,r.read()
def post(path,data):
    req=urllib.request.Request("http://127.0.0.1:8000"+path,data=json.dumps(data).encode(),
        headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=4) as r:return r.status,json.loads(r.read())
try:
    assert get("/")[0]==200
    assert json.loads(get("/api/dashboard")[1])["stores"]==3
    first=post("/api/automation/replenishment",{})[1]
    assert first["created_count"]==2,first
    second=post("/api/automation/replenishment",{})[1]
    assert second["created_count"]==0,second
    reps=json.loads(get("/api/replenishments")[1])["replenishments"]
    assert len(reps)==2 and all(x["status"]=="Pending Approval" for x in reps)
    rid=reps[0]["id"]
    approved=post(f"/api/replenishments/{rid}/decision",{"decision":"approve","manager":"Test Manager","reason":"Budget confirmed"})[1]
    assert approved["status"]=="Approved"
    # Repeated decision must be rejected.
    try:
        post(f"/api/replenishments/{rid}/decision",{"decision":"approve","manager":"Test Manager"})
        raise AssertionError("Duplicate decision unexpectedly accepted")
    except Exception as e:
        if isinstance(e,AssertionError): raise
    # Reject the second request and require a reason.
    rid2=[x["id"] for x in reps if x["id"]!=rid][0]
    rejected=post(f"/api/replenishments/{rid2}/decision",{"decision":"reject","manager":"Test Manager","reason":"Budget hold"})[1]
    assert rejected["status"]=="Rejected"
    # Case + POS route and high-severity approval
    status,case=post("/api/pos/reconcile",{"store":"Abu Dhabi Mall","category":"POS discrepancy","severity":"High","description":"Test till variance"})
    assert status==201 and case["tasks_created"]==2 and case["approval_required"]
    notes=json.loads(get("/api/notifications")[1])["notifications"]
    audit=json.loads(get("/api/audit")[1])["audit"]
    assert any(n["event_type"]=="replenishment.approve" for n in notes)
    assert any(n["event_type"]=="replenishment.reject" for n in notes)
    assert any(a["action"]=="replenishment.approve" for a in audit)
    assert any(a["action"]=="replenishment.reject" for a in audit)
    print("PASS: homepage/dashboard; 2 low-stock requests; rerun creates 0 duplicates; manager approve; manager reject; duplicate decision blocked; POS HTTP 201; 2 case tasks; notifications and audit decisions recorded.")
finally:
    server.shutdown();server.server_close()
    if DB_PATH.exists():DB_PATH.unlink()
