# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    """Extend CRM Lead / Opportunity with per-stage approval logic."""

    _inherit = 'crm.lead'

    # ------------------------------------------------------------------
    # Approval state fields
    # ------------------------------------------------------------------
    approval_state = fields.Selection(
        selection=[
            ('not_required', 'Not Required'),
            ('pending', 'Waiting Approval'),
            ('approved', 'Approved'),
            ('refused', 'Refused'),
        ],
        string='Approval Status',
        default='not_required',
        copy=False,
        tracking=True,
        help='Current approval status for the active stage.',
    )

    # Track where the opportunity came from so we can revert on refusal
    previous_stage_id = fields.Many2one(
        comodel_name='crm.stage',
        string='Previous Stage',
        copy=False,
        help='The stage the opportunity was in before moving to the current '
             'approval-required stage. Used to revert on rejection.',
    )

    approval_ids = fields.One2many(
        comodel_name='crm.lead.approval',
        inverse_name='lead_id',
        string='Approval History',
        copy=False,
    )

    approval_count = fields.Integer(
        string='Approvals',
        compute='_compute_approval_count',
        store=False,
    )

    current_stage_requires_approval = fields.Boolean(
        string='Stage Requires Approval',
        compute='_compute_current_stage_requires_approval',
        store=False,
    )

    can_current_user_approve = fields.Boolean(
        string='Can Approve',
        compute='_compute_can_current_user_approve',
        store=False,
    )

    # ------------------------------------------------------------------
    # Computed
    # ------------------------------------------------------------------
    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for lead in self:
            lead.approval_count = len(lead.approval_ids)

    @api.depends('stage_id', 'stage_id.require_approval')
    def _compute_current_stage_requires_approval(self):
        for lead in self:
            lead.current_stage_requires_approval = bool(
                lead.stage_id and lead.stage_id.require_approval
            )

    @api.depends('stage_id', 'stage_id.require_approval',
                 'stage_id.approval_type', 'stage_id.approval_user_id',
                 'stage_id.approval_group_id')
    def _compute_can_current_user_approve(self):
        for lead in self:
            lead.can_current_user_approve = (
                lead.stage_id.can_user_approve() if lead.stage_id else False
            )

    # ------------------------------------------------------------------
    # Override create and write – block stage transitions and manage states
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('stage_id'):
                stage = self.env['crm.stage'].browse(vals['stage_id'])
                if stage.require_approval:
                    vals['approval_state'] = 'pending'

        leads = super().create(vals_list)

        # Log pending approval and notify for newly created leads in approval stages
        for lead in leads:
            if lead.stage_id.require_approval:
                self.env['crm.lead.approval'].create({
                    'lead_id': lead.id,
                    'stage_id': lead.stage_id.id,
                    'approver_user_id': self.env.user.id,
                    'state': 'pending',
                })
                approver_partners = lead._get_approver_partner(lead.stage_id)
                lead.message_post(
                    body=Markup(_(
                        '<p>📋 <b>Approval Required</b> — '
                        'created in stage <b>%(stage)s</b></p>'
                        '<p>Created by: <b>%(user)s</b><br/>'
                        'The opportunity is now <b>awaiting approval</b>.</p>',
                        stage=lead.stage_id.name,
                        user=self.env.user.name,
                    )),
                    partner_ids=approver_partners.ids if approver_partners else [],
                    message_type='notification',
                    subtype_xmlid='mail.mt_note',
                )
        return leads

    def write(self, vals):
        """When a lead is moved into an approval-required stage:
        - Save the previous stage so we can revert on rejection.
        - Set approval_state to 'pending' automatically.
        - Create a pending log entry.
        - Notify the approver via chatter.

        Internal calls that pass 'approval_state': 'approved' bypass the
        locking (used by action_approve to finalise the move).
        """
        # Block stage transitions if current stage requires approval and is not approved yet
        if not self.env.context.get('skip_approval_check'):
            if 'stage_id' in vals:
                new_stage = self.env['crm.stage'].browse(vals['stage_id'])
                for lead in self:
                    if lead.stage_id and lead.stage_id.require_approval and lead.stage_id.id != new_stage.id:
                        if lead.approval_state != 'approved':
                            raise UserError(_(
                                'You cannot move opportunity "%(name)s" to another stage because '
                                'it is awaiting approval in stage "%(stage)s".'
                            ) % {
                                'name': lead.name,
                                'stage': lead.stage_id.name,
                            })

        # If moving to a stage that doesn't require approval, reset status
        if 'stage_id' in vals and 'approval_state' not in vals:
            new_stage = self.env['crm.stage'].browse(vals['stage_id'])
            if not new_stage.require_approval:
                vals['approval_state'] = 'not_required'
                vals['previous_stage_id'] = False

        # Collect leads whose stage is actually changing to an approval stage.
        # We do this BEFORE super() so we still have the old stage_id.
        leads_entering_approval = {}

        if 'stage_id' in vals and vals.get('approval_state') != 'approved':
            new_stage = self.env['crm.stage'].browse(vals['stage_id'])
            if new_stage.require_approval:
                for lead in self:
                    if lead.stage_id.id != new_stage.id:
                        # Remember the old stage for potential revert
                        leads_entering_approval[lead.id] = lead.stage_id.id

        result = super().write(vals)

        # After the write, handle approval pending state
        if leads_entering_approval:
            new_stage = self.env['crm.stage'].browse(vals['stage_id'])
            for lead in self.filtered(lambda l: l.id in leads_entering_approval):
                old_stage_id = leads_entering_approval[lead.id]
                # Write previous stage and pending state (bypass approval check
                # by not touching stage_id here)
                lead.with_context(skip_approval_check=True).write({
                    'previous_stage_id': old_stage_id,
                    'approval_state': 'pending',
                })
                # Log pending approval record
                self.env['crm.lead.approval'].create({
                    'lead_id': lead.id,
                    'stage_id': new_stage.id,
                    'approver_user_id': self.env.user.id,
                    'state': 'pending',
                })
                # Notify the approver
                approver_partners = lead._get_approver_partner(new_stage)
                if self.env.context.get('auto_stage_transition'):
                    body = Markup(_(
                        '<p>📋 <b>Approval Required</b> — '
                        'automatically moved to stage <b>%(stage)s</b></p>'
                        '<p>The opportunity is now <b>awaiting approval</b>.</p>',
                        stage=new_stage.name,
                    ))
                else:
                    body = Markup(_(
                        '<p>📋 <b>Approval Required</b> — '
                        'moved to stage <b>%(stage)s</b></p>'
                        '<p>Moved by: <b>%(user)s</b><br/>'
                        'The opportunity is now <b>awaiting approval</b>.</p>',
                        stage=new_stage.name,
                        user=self.env.user.name,
                    ))
                lead.message_post(
                    body=body,
                    partner_ids=(
                        approver_partners.ids if approver_partners else []
                    ),
                    message_type='notification',
                    subtype_xmlid='mail.mt_note',
                )

        return result

    # ------------------------------------------------------------------
    # Business logic – approve
    # ------------------------------------------------------------------
    def action_approve(self):
        """Approver grants approval for the current stage."""
        self.ensure_one()
        stage = self.stage_id

        if not stage.require_approval:
            raise UserError(
                _('The current stage "%s" does not require approval.') % stage.name
            )
        if not stage.can_user_approve():
            raise UserError(
                _('You are not authorised to approve opportunities at stage "%s".')
                % stage.name
            )
        if self.approval_state == 'approved':
            raise UserError(
                _('This opportunity is already approved for stage "%s".') % stage.name
            )

        # Mark the pending log entry as approved (or create a new one)
        pending = self.approval_ids.filtered(
            lambda a: a.stage_id == stage and a.state == 'pending'
        )
        if pending:
            pending[-1].write({
                'state': 'approved',
                'approver_user_id': self.env.user.id,
                'date': fields.Datetime.now(),
            })
        else:
            self.env['crm.lead.approval'].create({
                'lead_id': self.id,
                'stage_id': stage.id,
                'approver_user_id': self.env.user.id,
                'state': 'approved',
            })

        # Set approval_state to approved (bypass write lock)
        self.with_context(skip_approval_check=True).write({
            'approval_state': 'approved',
            'previous_stage_id': False,  # clear – no more revert needed
        })

        # Post chatter message (always tracked, appears as a note in the log)
        self.message_post(
            body=Markup(_(
                '<p>✅ <b>Approved</b></p>'
                '<p>Stage <b>%(stage)s</b> was approved by '
                '<b>%(user)s</b> on %(date)s.</p>',
                stage=stage.name,
                user=self.env.user.name,
                date=fields.Datetime.now().strftime('%d %b %Y %H:%M'),
            )),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

        # Automatically move to the next stage after approval
        next_stage_domain = [
            ('sequence', '>', stage.sequence),
        ]
        if self.team_id:
            next_stage_domain += ['|', ('team_ids', '=', False), ('team_ids', 'in', self.team_id.id)]
        else:
            next_stage_domain += [('team_ids', '=', False)]
        next_stage = self.env['crm.stage'].search(next_stage_domain, order='sequence asc, id asc', limit=1)
        if next_stage:
            self.with_context(skip_approval_check=True).write({
                'stage_id': next_stage.id,
            })

        return True

    # ------------------------------------------------------------------
    # Business logic – reject (opens wizard)
    # ------------------------------------------------------------------
    def action_refuse(self):
        """Open the rejection-reason wizard.
        The wizard will handle the actual refusal + stage revert + chatter log.
        """
        self.ensure_one()
        stage = self.stage_id

        if not stage.require_approval:
            raise UserError(
                _('The current stage "%s" does not require approval.') % stage.name
            )
        if not stage.can_user_approve():
            raise UserError(
                _('You are not authorised to reject opportunities at stage "%s".')
                % stage.name
            )

        return {
            'type': 'ir.actions.act_window',
            'name': _('Rejection Reason'),
            'res_model': 'crm.lead.refuse.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lead_id': self.id,
                'default_stage_id': stage.id,
            },
        }

    # ------------------------------------------------------------------
    # Reset helper (called from wizard or manual reset)
    # ------------------------------------------------------------------
    def action_reset_approval(self):
        """Reset approval status so a new approval request can be made."""
        self.ensure_one()
        self.with_context(skip_approval_check=True).write({
            'approval_state': (
                'not_required' if not self.stage_id.require_approval else 'pending'
            ),
        })
        return True

    # ------------------------------------------------------------------
    # Helper – get partner(s) to notify
    # ------------------------------------------------------------------
    def _get_approver_partner(self, stage):
        """Return the res.partner record(s) to notify for a given stage."""
        self.ensure_one()
        if stage.approval_type == 'user' and stage.approval_user_id:
            return stage.approval_user_id.partner_id
        elif stage.approval_type == 'group' and stage.approval_group_id:
            users = stage.approval_group_id.user_ids.filtered(
                lambda u: not u.share and u.active
            )
            return users.mapped('partner_id')
        return self.env['res.partner']

    def action_view_approvals(self):
        """Open the approval history for this opportunity."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Approval History'),
            'res_model': 'crm.lead.approval',
            'view_mode': 'list,form',
            'domain': [('lead_id', '=', self.id)],
            'context': {'default_lead_id': self.id},
        }
