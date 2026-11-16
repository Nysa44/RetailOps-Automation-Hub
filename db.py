import sqlite3
from pathlib import Path
DB_PATH=Path(__file__).with_name("retailops.db")
def get_db():
    c=sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c
def init_db():
    with get_db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS stores(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS inventory(
          id INTEGER PRIMARY KEY, store TEXT NOT NULL, sku TEXT NOT NULL, product TEXT NOT NULL,
          on_hand INTEGER NOT NULL CHECK(on_hand>=0), reorder_level INTEGER NOT NULL CHECK(reorder_level>=0),
          UNIQUE(store,sku));
        CREATE TABLE IF NOT EXISTS cases(
          id INTEGER PRIMARY KEY AUTOINCREMENT, store TEXT NOT NULL, category TEXT NOT NULL,
          severity TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Open',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS tasks(
          id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL REFERENCES cases(id),
          task TEXT NOT NULL, owner TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending');
        CREATE TABLE IF NOT EXISTS approvals(
          id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL REFERENCES cases(id),
          approver TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'Pending');
        CREATE TABLE IF NOT EXISTS replenishment(
          id INTEGER PRIMARY KEY AUTOINCREMENT, store TEXT NOT NULL, sku TEXT NOT NULL,
          product TEXT NOT NULL, quantity INTEGER NOT NULL, idempotency_key TEXT NOT NULL UNIQUE,
          status TEXT NOT NULL DEFAULT 'Pending Approval', requested_by TEXT NOT NULL DEFAULT 'Automation',
          decided_by TEXT, decision_reason TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          decided_at TEXT);
        CREATE TABLE IF NOT EXISTS notifications(
          id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT NOT NULL, related_type TEXT NOT NULL,
          related_id INTEGER NOT NULL, message TEXT NOT NULL, recipient TEXT NOT NULL DEFAULT 'Operations',
          channel TEXT NOT NULL DEFAULT 'In-app', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS audit_log(
          id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, entity_type TEXT NOT NULL,
          entity_id INTEGER NOT NULL, actor TEXT NOT NULL, details TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        """)
        if c.execute("SELECT COUNT(*) FROM stores").fetchone()[0]==0:
            c.executemany("INSERT INTO stores(name) VALUES(?)",[
              ("Abu Dhabi Mall",),("Yas Mall",),("Dubai Mall",)])
            c.executemany("""INSERT INTO inventory(store,sku,product,on_hand,reorder_level)
              VALUES(?,?,?,?,?)""",[
              ("Abu Dhabi Mall","SKU-100","Wireless earbuds",3,5),
              ("Abu Dhabi Mall","SKU-200","Smart watch",12,4),
              ("Yas Mall","SKU-100","Wireless earbuds",2,5),
              ("Yas Mall","SKU-300","Portable speaker",3,3),
              ("Dubai Mall","SKU-200","Smart watch",7,4),
              ("Dubai Mall","SKU-400","Phone charger",18,6)])
        c.commit()
