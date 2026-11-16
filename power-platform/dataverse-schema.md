# Dataverse schema blueprint

| Table | Suggested columns | Notes |
|---|---|---|
| Retail Store | Store Name, Store Code, Region, Active | Store directory |
| Inventory Snapshot | Store (lookup), SKU, Product, On Hand, Reorder Level, Last Sync | Stock position |
| Operations Case | Case Number, Store (lookup), Category, Severity, Description, Status, Created On | Exception queue |
| Workflow Task | Case (lookup), Task Name, Owner, Due Date, Status | Two standard tasks per case |
| Case Approval | Case (lookup), Approver, Decision, Comments, Decision Date | High/Critical case approval |
| Replenishment Request | Store (lookup), SKU, Product, Quantity, Idempotency Key, Status, Requested By, Decided By, Decision Reason, Decided At | Manager approval queue |
| Audit Event | Event Type, Related Record, Actor, Details, Created On | Traceability |
| Notification | Event Type, Related Record, Message, Recipient, Channel, Created On | In-app notification |

Recommended alternate key: `Idempotency Key` on Replenishment Request. Configure security roles for Store Operator, Operations Lead and Regional Manager.
