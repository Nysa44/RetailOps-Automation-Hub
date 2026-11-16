# RetailOps Automation Hub v2

A functional retail operations workflow demo using Python 3.9+, SQLite and browser JavaScript. No third-party Python packages are required.

## Run
1. Extract the ZIP.
2. Open the project folder in a terminal.
3. Run `python app.py`.
4. Open `http://localhost:8000`.

The SQLite database is created and seeded automatically on first launch. Stop the app and delete `retailops.db` to reset the demo.

## Implemented features
- Three simulated UAE retail stores and six inventory records.
- Low-stock scan creates replenishment requests for below-threshold items.
- Requests enter `Pending Approval` and appear in the manager queue.
- Manager can approve or reject a request from the dashboard; a manager name is required and rejection requires a reason.
- A decision can only be made once. Subsequent automation runs skip active Pending Approval or Approved requests for that store/SKU.
- Notifications for request creation and manager decisions.
- Audit events for automation runs, replenishment creation, approvals, rejections and exception creation.
- POS reconciliation endpoint and exception routing with two tasks; High/Critical cases create a separate case approval record.
- Dashboard, inventory, approval queue, notifications and audit history.

## API
- `GET /api/health`
- `GET /api/dashboard`
- `GET /api/cases`
- `GET /api/inventory`
- `GET /api/replenishments`
- `GET /api/notifications`
- `GET /api/audit`
- `POST /api/cases`
- `POST /api/pos/reconcile`
- `POST /api/automation/replenishment`
- `POST /api/replenishments/{id}/decision` with JSON `{ "decision":"approve|reject", "manager":"Name", "reason":"..." }`

## Clean database verification
Run `python verify.py`. The test resets the demo database, exercises the HTTP endpoints, tests duplicate prevention, approval, rejection, duplicate-decision protection, POS reconciliation, notifications and audit history, then removes the test database.

## Power Platform assets
See `power-platform/`. These are build specifications and starter assets, not a deployed Microsoft Power Platform solution. Import/configure them in a Power Platform environment before claiming native deployment.
