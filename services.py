import json
from db import get_db
CATEGORIES={"POS discrepancy","Inventory shortage","Loyalty issue","Customer refund"}
SEVERITIES={"Low","Medium","High","Critical"}

def _audit(c,action,entity_type,entity_id,actor,details):
    c.execute("""INSERT INTO audit_log(action,entity_type,entity_id,actor,details)
                 VALUES(?,?,?,?,?)""",(action,entity_type,entity_id,actor,json.dumps(details,sort_keys=True)))
def _notify(c,event,kind,rid,message,recipient="Operations"):
    c.execute("""INSERT INTO notifications(event_type,related_type,related_id,message,recipient)
                 VALUES(?,?,?,?,?)""",(event,kind,rid,message,recipient))

def create_case(data):
    category=data.get("category","POS discrepancy")
    severity=data.get("severity","Medium")
    store=(data.get("store") or "Abu Dhabi Mall").strip()
    description=(data.get("description") or "Operational exception").strip()
    if category not in CATEGORIES: raise ValueError("Unsupported exception category")
    if severity not in SEVERITIES: raise ValueError("Invalid severity")
    if not store or not description: raise ValueError("Store and description are required")
    with get_db() as c:
        cur=c.execute("INSERT INTO cases(store,category,severity,description) VALUES(?,?,?,?)",
                      (store,category,severity,description))
        cid=cur.lastrowid
        c.executemany("INSERT INTO tasks(case_id,task,owner) VALUES(?,?,?)",[
          (cid,"Validate exception details","Store Operations"),
          (cid,"Resolve and update case","Operations Lead")])
        _notify(c,"case.created","case",cid,f"New {severity.lower()} {category.lower()} case at {store}")
        approval=severity in ("High","Critical")
        if approval:
            c.execute("INSERT INTO approvals(case_id,approver) VALUES(?,?)",(cid,"Regional Manager"))
        _audit(c,"case.created","case",cid,"System",{"store":store,"category":category,"severity":severity})
        c.commit()
        return {"id":cid,"status":"Open","tasks_created":2,"approval_required":approval}

def run_replenishment():
    created=[]
    with get_db() as c:
        rows=c.execute("""SELECT * FROM inventory WHERE on_hand < reorder_level
                          ORDER BY store,sku""").fetchall()
        for r in rows:
            # One active request per store/SKU; a rejected request may be retried with a new cycle key.
            active=c.execute("""SELECT id FROM replenishment WHERE store=? AND sku=?
                                AND status IN ('Pending Approval','Approved')""",(r["store"],r["sku"])).fetchone()
            if active: continue
            cycle=c.execute("SELECT COUNT(*) FROM replenishment WHERE store=? AND sku=?",
                            (r["store"],r["sku"])).fetchone()[0]+1
            key=f"replenish:{r['store']}:{r['sku']}:cycle:{cycle}"
            qty=max((r["reorder_level"]*2)-r["on_hand"],1)
            cur=c.execute("""INSERT OR IGNORE INTO replenishment
                (store,sku,product,quantity,idempotency_key,status)
                VALUES(?,?,?,?,?,'Pending Approval')""",
                (r["store"],r["sku"],r["product"],qty,key))
            if cur.rowcount:
                rid=cur.lastrowid
                created.append({"id":rid,"store":r["store"],"sku":r["sku"],"quantity":qty})
                _notify(c,"replenishment.requested","replenishment",rid,
                        f"Replenishment request #{rid} for {r['product']} at {r['store']} awaits manager approval",
                        "Regional Manager")
                _audit(c,"replenishment.created","replenishment",rid,"Automation",
                       {"store":r["store"],"sku":r["sku"],"quantity":qty,"idempotency_key":key})
        _audit(c,"replenishment.run","automation",0,"Automation",{"new_requests":len(created)})
        c.commit()
    return {"created":created,"created_count":len(created),"duplicate_prevented":True}

def decide_replenishment(request_id,data):
    decision=(data.get("decision") or "").strip().lower()
    actor=(data.get("manager") or data.get("actor") or "").strip()
    reason=(data.get("reason") or "").strip()
    if decision not in ("approve","reject"): raise ValueError("Decision must be approve or reject")
    if not actor: raise ValueError("Manager name is required")
    with get_db() as c:
        row=c.execute("SELECT * FROM replenishment WHERE id=?",(request_id,)).fetchone()
        if not row: raise LookupError("Replenishment request not found")
        if row["status"]!="Pending Approval": raise ValueError("Only pending requests can be decided")
        status="Approved" if decision=="approve" else "Rejected"
        c.execute("""UPDATE replenishment SET status=?,decided_by=?,decision_reason=?,decided_at=CURRENT_TIMESTAMP
                     WHERE id=? AND status='Pending Approval'""",(status,actor,reason,request_id))
        if c.total_changes==0: raise ValueError("Request has already been decided")
        _notify(c,f"replenishment.{decision}","replenishment",request_id,
                f"Replenishment request #{request_id} was {status.lower()} by {actor}"+
                (f": {reason}" if reason else ""),"Store Operations")
        _audit(c,f"replenishment.{decision}","replenishment",request_id,actor,
               {"status":status,"reason":reason,"store":row["store"],"sku":row["sku"]})
        c.commit()
        return {"id":request_id,"status":status,"manager":actor,"reason":reason}

def dashboard_data():
    with get_db() as c:
        scalar=lambda q:c.execute(q).fetchone()[0]
        return {
          "stores":scalar("SELECT COUNT(*) FROM stores"),
          "inventory_records":scalar("SELECT COUNT(*) FROM inventory"),
          "open_cases":scalar("SELECT COUNT(*) FROM cases WHERE status='Open'"),
          "pending_approvals":scalar("SELECT COUNT(*) FROM replenishment WHERE status='Pending Approval'"),
          "replenishment_requests":scalar("SELECT COUNT(*) FROM replenishment"),
          "low_stock_items":scalar("SELECT COUNT(*) FROM inventory WHERE on_hand < reorder_level"),
          "recent_cases":[dict(r) for r in c.execute("SELECT id,store,category,severity,status FROM cases ORDER BY id DESC LIMIT 5")]
        }
def list_cases():
    with get_db() as c:return [dict(r) for r in c.execute("SELECT * FROM cases ORDER BY id DESC")]
def list_inventory():
    with get_db() as c:return [dict(r) for r in c.execute("SELECT * FROM inventory ORDER BY store,sku")]
def list_replenishments():
    with get_db() as c:return [dict(r) for r in c.execute("SELECT * FROM replenishment ORDER BY id DESC")]
def list_notifications():
    with get_db() as c:return [dict(r) for r in c.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 100")]
def list_audit():
    with get_db() as c:return [dict(r) for r in c.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 150")]
