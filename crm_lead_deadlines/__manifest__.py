# -*- coding: utf-8 -*-
{
    'name': 'CRM Lead Deadlines and Lead Source Extension',
    'version': '19.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Custom CRM deadlines, lead source, and per-stage pipeline Kanban sorting',
    'description': """
CRM Lead Deadlines & Stage Sorting Extension
============================================
- Adds three custom deadline fields:
  * Design Deadline (x_design_presentation_deadline)
  * Client Submission Deadline (x_client_submission_deadline)
  * Commercial Proposal Deadline (x_commercial_proposition_deadline)
- Adds Event and Lead Source tracking fields.
- Allows configuring per-stage deadline sorting on CRM Stages so opportunities
  in the pipeline Kanban view are automatically sorted by that stage's deadline date.
    """,
    'author': 'Mohammed Juraige',
    'website': 'https://github.com/mohammedjuraige-dev',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_views.xml',
        'views/crm_stage_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
