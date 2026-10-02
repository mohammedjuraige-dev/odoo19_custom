# -*- coding: utf-8 -*-
{
    'name': 'CRM Pipeline Stage Approval',
    'version': '19.0.1.1.0',
    'category': 'Sales/CRM',
    'summary': 'Add multi-level approval workflows to CRM pipeline stages',
    'description': """
        CRM Pipeline Stage Approval
        ===========================
        This module adds a configurable approval system to CRM pipeline stages.

        Features:
        ---------
        - Enable approval requirement on any CRM pipeline stage
        - Choose approver by specific user OR by user group
        - Multi-level approval: each stage can have its own approver
        - Approval history log on every opportunity
        - Kanban status indicator for pending/approved/refused states
        - Block stage transitions until approval is granted
        - Notify approvers via Odoo internal messaging
    """,
    'author': 'Custom Development',
    'depends': ['crm', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'security/crm_approval_security.xml',
        'views/crm_stage_views.xml',
        'views/crm_lead_refuse_wizard_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
