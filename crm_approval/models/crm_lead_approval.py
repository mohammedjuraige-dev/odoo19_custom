# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmLeadApproval(models.Model):
    """Approval log line – one record per stage-approval action."""

    _name = 'crm.lead.approval'
    _description = 'CRM Lead / Opportunity Approval Line'
    _order = 'date desc, id desc'
    _rec_name = 'stage_id'

    lead_id = fields.Many2one(
        comodel_name='crm.lead',
        string='Opportunity',
        required=True,
        ondelete='cascade',
        index=True,
    )
    stage_id = fields.Many2one(
        comodel_name='crm.stage',
        string='Stage',
        required=True,
        ondelete='restrict',
    )
    approver_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approved / Refused By',
        required=True,
        default=lambda self: self.env.user,
    )
    state = fields.Selection(
        selection=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
        ],
        string='Status',
        default='pending',
        required=True,
    )
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
    )
    note = fields.Text(string='Note / Reason')

    # Display helpers
    state_label = fields.Char(
        string='Status Label',
        compute='_compute_state_label',
        store=False,
    )

    @api.depends('state')
    def _compute_state_label(self):
        labels = {'pending': 'Pending', 'approved': 'Approved', 'refused': 'Refused'}
        for rec in self:
            rec.state_label = labels.get(rec.state, rec.state)
