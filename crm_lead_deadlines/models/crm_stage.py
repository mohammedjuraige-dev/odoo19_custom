# -*- coding: utf-8 -*-
from odoo import models, fields


class CrmStage(models.Model):
    _inherit = 'crm.stage'

    deadline_sort_field_id = fields.Many2one(
        'ir.model.fields',
        string='Deadline Sort Field',
        domain="[('model', '=', 'crm.lead'), ('name', 'in', ('x_design_presentation_deadline', 'x_client_submission_deadline', 'x_commercial_proposition_deadline'))]",
        ondelete='set null',
        help="Select which deadline field should be used to sort opportunities in this stage in the pipeline Kanban view."
    )
    deadline_sort_order = fields.Selection(
        selection=[
            ('asc', 'Ascending (Earliest Deadline First)'),
            ('desc', 'Descending (Latest Deadline First)'),
        ],
        string='Sort Direction',
        default='asc',
        help="Choose whether opportunities are sorted ascending (earliest deadline first) or descending (latest deadline first)."
    )
