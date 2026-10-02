# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CrmStage(models.Model):
    """Extend CRM Stage to support per-stage approval configuration."""

    _inherit = 'crm.stage'

    # ------------------------------------------------------------------
    # Approval toggle
    # ------------------------------------------------------------------
    require_approval = fields.Boolean(
        string='Require Approval',
        default=False,
        help='When enabled, opportunities must be approved before they can '
             'be moved into (or remain in) this stage.',
    )

    # ------------------------------------------------------------------
    # Approver type: user or group
    # ------------------------------------------------------------------
    approval_type = fields.Selection(
        selection=[
            ('user', 'Specific User'),
            ('group', 'User Group'),
        ],
        string='Approver Type',
        default='user',
        help='Choose whether a specific user or any member of a group can '
             'approve opportunities at this stage.',
    )

    approval_user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver',
        domain=[('share', '=', False)],
        help='The specific internal user who must approve this stage.',
    )

    approval_group_id = fields.Many2one(
        comodel_name='res.groups',
        string='Approver Group',
        help='Any member of this group can approve opportunities at this stage.',
    )

    # ------------------------------------------------------------------
    # Computed display helpers
    # ------------------------------------------------------------------
    approval_display = fields.Char(
        string='Approval Required By',
        compute='_compute_approval_display',
        store=False,
    )

    @api.depends('require_approval', 'approval_type', 'approval_user_id',
                 'approval_group_id')
    def _compute_approval_display(self):
        for stage in self:
            if not stage.require_approval:
                stage.approval_display = 'No approval required'
            elif stage.approval_type == 'user' and stage.approval_user_id:
                stage.approval_display = stage.approval_user_id.name
            elif stage.approval_type == 'group' and stage.approval_group_id:
                stage.approval_display = stage.approval_group_id.full_name
            else:
                stage.approval_display = 'Approval required (approver not set)'

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('require_approval', 'approval_type',
                    'approval_user_id', 'approval_group_id')
    def _check_approval_config(self):
        for stage in self:
            if stage.require_approval:
                if stage.approval_type == 'user' and not stage.approval_user_id:
                    raise ValidationError(
                        f'Stage "{stage.name}": Please set an approver user '
                        f'when "Require Approval" is enabled with type "Specific User".'
                    )
                if stage.approval_type == 'group' and not stage.approval_group_id:
                    raise ValidationError(
                        f'Stage "{stage.name}": Please set an approver group '
                        f'when "Require Approval" is enabled with type "User Group".'
                    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def can_user_approve(self, user=None):
        """Return True if *user* (defaults to env.user) is allowed to approve
        opportunities at this stage."""
        self.ensure_one()
        if not self.require_approval:
            return True
        user = user or self.env.user
        if self.approval_type == 'user':
            return user == self.approval_user_id
        elif self.approval_type == 'group':
            return self.approval_group_id in user.group_ids
        return False
