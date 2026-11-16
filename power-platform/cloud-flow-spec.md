# Power Automate cloud-flow specifications

## Flow A — Scheduled low-stock replenishment
**Trigger:** Recurrence (for example hourly) or inventory snapshot update.
1. List Inventory Snapshot rows where On Hand is less than Reorder Level.
2. Compose a stable store + SKU + replenishment-cycle idempotency key.
3. Check for an existing Pending Approval or Approved request for that store/SKU.
4. If none exists, create a Replenishment Request with status Pending Approval and calculated quantity.
5. Notify Regional Manager and create an Audit Event.
6. Use scoped error handling, retries and run-after branches.

## Flow B — Manager approval
**Trigger:** When a Replenishment Request is created with status Pending Approval.
1. Start and wait for an approval assigned to the Regional Manager.
2. On Approve, update status, decision maker and decision timestamp.
3. On Reject, require/store a rejection reason and update status.
4. Notify Store Operations of the decision.
5. Write an Audit Event with request ID, actor, outcome and reason.
6. Ensure the row is updated only if it remains Pending Approval to prevent double decisions.

## Flow C — Exception intake and routing
**Trigger:** When an Operations Case row is added.
1. Create two Workflow Task rows: validate details; resolve and update.
2. If severity is High or Critical, start and wait for approval assigned to Regional Manager.
3. Create a Notification and send the configured Teams/email notification.
4. Update case status and write an Audit Event.

## Flow D — POS reconciliation
**Trigger:** POS reconciliation exception received from connector or Canvas App.
1. Validate store and transaction reference.
2. Create Operations Case with category POS discrepancy.
3. Let Flow C route tasks, approvals and notifications.

Before production, configure connection references, environment variables, permissions, retry policy, failure alerts and data retention.
