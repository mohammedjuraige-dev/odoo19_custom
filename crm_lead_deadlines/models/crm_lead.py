# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # -------------------------------------------------------------------
    # Deadline fields (shown after "Expected Closing" on the form/tree)
    # -------------------------------------------------------------------
    x_design_presentation_deadline = fields.Date(string='Design Deadline')
    x_client_submission_deadline = fields.Date(string='Client Submission Deadline')
    x_commercial_proposition_deadline = fields.Date(string='Commercial Proposal Deadline')

    # -------------------------------------------------------------------
    # Event / lead-source fields (shown after Phone on Lead & Opportunity)
    # -------------------------------------------------------------------
    x_contact_person = fields.Char(string='Contact Person')
    x_event_name = fields.Char(string='Event Name')
    x_event_dates = fields.Char(string='Event Dates')
    x_event_location = fields.Char(string='Event Location')
    x_lead_sources = fields.Selection(
        selection=[
            ('direct_client', 'Direct Client'),
            ('google_form', 'Google Form - Company Client'),
            ('whatsapp', 'WhatsApp - Company Client'),
            ('inbound_calls', 'Inbound Calls - Company Client'),
            ('direct_email', 'Direct Email - Company Client'),
            ('facebook', 'Facebook - Company Client'),
            ('instagram', 'Instagram - Company Client'),
            ('linkedin', 'LinkedIn - Company Client'),
            ('website', 'Website - Company Client'),
        ],
        string='Lead Source',
    )
    x_size = fields.Char(string='Size')

    # -------------------------------------------------------------------
    # Per-stage Kanban sorting based on stage's configured deadline field
    # -------------------------------------------------------------------
    @api.model
    def _extract_single_stage_id(self, domain):
        """Extract a single stage_id if domain filters on exactly one stage."""
        if not domain:
            return None
        try:
            from odoo.fields import Domain
            domain_obj = Domain(domain)
            stage_ids = set()
            has_negative_or_multi = False
            for leaf in domain_obj.iter_conditions():
                if leaf.field_expr == 'stage_id':
                    if leaf.operator == '=' and isinstance(leaf.value, int):
                        stage_ids.add(leaf.value)
                    elif leaf.operator == 'in' and isinstance(leaf.value, (list, tuple)):
                        if len(leaf.value) == 1 and isinstance(leaf.value[0], int):
                            stage_ids.add(leaf.value[0])
                        else:
                            has_negative_or_multi = True
                    else:
                        has_negative_or_multi = True
            if not has_negative_or_multi and len(stage_ids) == 1:
                return next(iter(stage_ids))
        except Exception:
            pass
        return None

    @api.model
    def _get_stage_deadline_order(self, domain, order=None):
        """Prepend stage-configured deadline sort field to order if domain targets a single stage."""
        stage_id = self._extract_single_stage_id(domain)
        if stage_id:
            stage = self.env['crm.stage'].sudo().browse(stage_id)
            if stage.exists() and stage.deadline_sort_field_id:
                field_name = stage.deadline_sort_field_id.name
                if field_name in self._fields:
                    direction = (stage.deadline_sort_order or 'asc').upper()
                    stage_order_clause = f"{field_name} {direction} NULLS LAST"
                    base_order = order or self._order
                    if field_name not in base_order:
                        return f"{stage_order_clause}, {base_order}"
        return order

    @api.model
    def search_fetch(self, domain, field_names=None, offset=0, limit=None, order=None):
        order = self._get_stage_deadline_order(domain, order)
        return super().search_fetch(domain, field_names=field_names, offset=offset, limit=limit, order=order)

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        order = self._get_stage_deadline_order(domain, order)
        return super()._search(domain, offset=offset, limit=limit, order=order, **kwargs)

