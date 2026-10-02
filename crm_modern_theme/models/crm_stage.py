# -*- coding: utf-8 -*-

from odoo import api, fields, models

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    hide_quick_create = fields.Boolean(
        string="Hide Quick Add",
        default=False,
        help="Hide the quick add (+) button on this stage in the CRM kanban view."
    )
    is_quick_create_allowed = fields.Boolean(
        compute='_compute_is_quick_create_allowed',
        help="Technical field to determine if the current user can quick-create leads in this stage."
    )

    @api.depends('hide_quick_create')
    def _compute_is_quick_create_allowed(self):
        is_in_group = self.env.user.has_group('crm_modern_theme.group_crm_quick_add') or self.env.is_admin() or self.env.su
        for stage in self:
            if not stage.hide_quick_create:
                stage.is_quick_create_allowed = True
            else:
                stage.is_quick_create_allowed = is_in_group
