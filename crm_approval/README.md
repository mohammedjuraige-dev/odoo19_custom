# CRM Pipeline Stage Approval User Guide

The **CRM Pipeline Stage Approval** module adds a multi-level approval system to CRM pipeline stages in Odoo 19. This allows managers to ensure that key conditions are met before opportunities progress further in the sales cycle.

---

## 1. Installation

1. Make sure the module directory `crm_approval` is placed inside your Odoo custom addons directory.
2. Restart the Odoo server.
3. Log in to Odoo as an Administrator and activate **Developer Mode** (Settings -> Activate the developer mode).
4. Navigate to the **Apps** dashboard.
5. Click **Update Apps List** in the top menu bar, then click **Update**.
6. Search for `CRM Pipeline Stage Approval` (or technical name `crm_approval`) in the search bar.
7. Click **Activate** (or **Upgrade** if already installed).

---

## 2. Configuring Stages for Approval

Once installed, you can configure any pipeline stage to require approval before opportunities can progress:

1. Navigate to **CRM** -> **Configuration** -> **Stages**.
2. Click on the stage you want to protect (e.g., *Proposition* or *Negotiation*).
3. Check the **Require Approval** checkbox.
4. Select the **Approver Type**:
   - **Specific User**: Only a single designated user can grant approval. Select that user in the **Approver** field.
   - **User Group**: Any member of a specific user group can grant approval. Select the group in the **Approver Group** field.
5. Save the stage configuration.

---

## 3. The Approval Workflow

### Dragging Opportunities into an Approval Stage
- When a salesperson drags or moves an opportunity into an approval-protected stage:
  1. The opportunity is marked with a **"Waiting Approval"** status ribbon.
  2. The opportunity's stage transitions are **locked**—it cannot be moved to any other stage until approval is granted.
  3. A log entry is created in the **Approval History**.
  4. The designated approver(s) are notified via Odoo internal messaging, and a note is posted in the opportunity's chatter.

### Approving an Opportunity
- When the designated approver views the opportunity, they will see an **Approve** and a **Reject** button in the header.
- Clicking **Approve**:
  1. Grants approval for the current stage.
  2. Updates the opportunity status to **"Approved"**.
  3. Unlocks the opportunity so that it can be moved to any subsequent pipeline stage.
  4. Posts a success note to the chatter.

### Rejecting / Refusing an Opportunity
- If the opportunity does not meet requirements, the approver can click **Reject**:
  1. A wizard will open asking for a **Rejection Reason**.
  2. Enter the reason and click **Confirm Rejection**.
  3. The opportunity is **automatically reverted** to its previous pipeline stage.
  4. The status resets to normal.
  5. The rejection reason and the name of the approver are logged in detail to the opportunity's chatter for full transparency.

---

## 4. Audit Trail & History Logs

- On every opportunity form, an **Approval History** tab is displayed at the bottom showing:
  - The date of each approval/rejection request.
  - The stage requiring approval.
  - The user who approved or rejected the opportunity.
  - The status (`Pending`, `Approved`, or `Refused`).
  - Notes or rejection reasons entered.
- Managers can view a global audit log of all approval requests across the company by navigating to **CRM** -> **Reporting** -> **Approval History**.
