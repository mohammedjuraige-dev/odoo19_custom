# -*- coding: utf-8 -*-

from odoo import api, models

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def web_read_group(self, domain, groupby, aggregates=(), limit=None, offset=0, order=None, **kwargs):
        # Ensure that color is fetched from crm.stage if grouping by stage_id
        groupby_read_specification = kwargs.setdefault('groupby_read_specification', {})
        for g_spec in groupby:
            fname = g_spec.split(':')[0]
            if fname == 'stage_id':
                stage_spec = groupby_read_specification.setdefault(g_spec, {})
                stage_spec['color'] = {}
                stage_spec['is_quick_create_allowed'] = {}
        return super().web_read_group(domain, groupby, aggregates, limit=limit, offset=offset, order=order, **kwargs)
