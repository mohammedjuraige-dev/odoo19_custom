# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmLeadRefuseWizard(models.TransientModel):
    """Transient wizard that captures a rejection reason, reverts the
    opportunity to its previous pipeline stage and logs everything in
    the chatter."""

    _name = 'crm.lead.refuse.wizard'
    _description = 'CRM Lead Approval – Rejection Reason Wizard'

    lead_id = fields.Many2one(
        comodel_name='crm.lead',
        string='Opportunity',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    stage_id = fields.Many2one(
        comodel_name='crm.stage',
        string='Rejected Stage',
        required=True,
        readonly=True,
    )
    previous_stage_id = fields.Many2one(
        comodel_name='crm.stage',
        string='Revert To Stage',
        compute='_compute_previous_stage_id',
        store=False,
    )
    reason = fields.Text(
        string='Rejection Reason',
        required=True,
        help='Please explain why this opportunity is being rejected. '
             'This note will be visible in the opportunity chatter.',
    )

    @api.depends('lead_id')
    def _compute_previous_stage_id(self):
        for wiz in self:
            wiz.previous_stage_id = wiz.lead_id.previous_stage_id

    # ------------------------------------------------------------------
    # Confirm rejection
    # ------------------------------------------------------------------
    def action_confirm_refuse(self):
        """Perform the rejection:
        1. Mark the pending approval log as 'refused'.
        2. Revert the opportunity to its previous stage (bypassing the
           approval-required write guard so we don't recurse).
        3. Reset approval_state and clear previous_stage_id.
        4. Post a chatter message with the rejection reason.
        """
        self.ensure_one()
        lead = self.lead_id
        stage = self.stage_id

        if not stage.can_user_approve():
            raise UserError(
                _('You are not authorised to reject opportunities at stage "%s".')
                % stage.name
            )

        # 1. Update the pending approval log
        pending = lead.approval_ids.filtered(
            lambda a: a.stage_id == stage and a.state == 'pending'
        )
        if pending:
            pending[-1].write({
                'state': 'refused',
                'approver_user_id': self.env.user.id,
                'date': fields.Datetime.now(),
                'note': self.reason,
            })
        else:
            self.env['crm.lead.approval'].create({
                'lead_id': lead.id,
                'stage_id': stage.id,
                'approver_user_id': self.env.user.id,
                'state': 'refused',
                'note': self.reason,
            })

        # 2. Revert to previous stage (or keep current if no previous)
        revert_stage = lead.previous_stage_id or stage

        # Determine what approval_state should be after revert:
        #  - If the revert stage also requires approval → 'pending'
        #    (rare edge case; the next drag will overwrite this anyway)
        #  - Otherwise → 'not_required'
        # We deliberately do NOT leave it as 'refused' because the lead
        # is now in a non-approval stage and showing "Refused" there is
        # misleading.  The full rejection history is preserved in approval_ids.
        post_revert_state = (
            'pending' if revert_stage.require_approval else 'not_required'
        )

        # Use with_context to bypass the approval write guard
        lead.with_context(skip_approval_check=True).write({
            'stage_id': revert_stage.id,
            'approval_state': post_revert_state,
            'previous_stage_id': False,
        })

        # 3. Post chatter message – this shows in the chatter/log
        lead.message_post(
            body=Markup(_(
                '<p>❌ <b>Rejected</b> — stage <b>%(stage)s</b></p>'
                '<p>Rejected by: <b>%(user)s</b> on %(date)s</p>'
                '<p><b>Reason:</b> %(reason)s</p>'
                '<p>The opportunity has been reverted to stage '
                '<b>%(prev_stage)s</b>.</p>',
                stage=stage.name,
                user=self.env.user.name,
                date=fields.Datetime.now().strftime('%d %b %Y %H:%M'),
                reason=self.reason,
                prev_stage=revert_stage.name,
            )),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

        return {'type': 'ir.actions.act_window_close'}
