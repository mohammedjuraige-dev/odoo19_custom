# -*- coding: utf-8 -*-
{
    'name': 'CRM Modern Theme',
    'version': '19.0.1.0.0',
    'category': 'Customizations',
    'summary': 'A modern visual refresh for the CRM Pipeline, Leads, and forms (CSS-only)',
    'description': """
CRM Modern Theme
=================
A pure front-end visual refresh for the CRM app. Inspired by modern SaaS CRM
boards (Pipedrive / HubSpot style pipelines): soft neutral backgrounds, card
elevation on hover, a colour-cycled accent strip per pipeline stage, refined
typography, pill tags, and a cleaner list/form layout.

Verified directly against the Odoo 19.0 core source (addons/crm and
addons/web on the 19.0 branch) — every view id, xpath target, and CSS
selector this module relies on was checked line-by-line against the real
19.0 templates rather than assumed from the 18.0 version. Three selectors
that quietly changed name between 18.0 and 19.0 were updated so the theme
keeps working instead of silently going dead: the list header sort icon
class, the kanban column progress-bar markup, and the empty-state helper
class.

What this module changes
-------------------------
* Adds SCSS to the ``web.assets_backend`` bundle (pure CSS, compiled by Odoo's
  own asset pipeline — nothing is injected from outside).
* Adds a CSS marker class (``o_crm_theme_kanban_leads`` / ``o_crm_theme_list`` /
  ``o_crm_theme_form``) to the root tag of a few existing CRM views, using
  Odoo's additive ``<attribute name="class" add="..." separator=" "/>``
  syntax. This *appends* a class name; it never replaces or removes an
  existing attribute, so it cannot collide with classes added by other
  modules (including Odoo Enterprise) on the same view.

What this module does NOT change
---------------------------------
* No field, button, group, workflow, automation, security rule, report, or
  Python method is added, removed, or modified.
* The Pipeline kanban (``crm.crm_case_kanban_view_leads``) already ships its
  own unique class (``o_opportunity_kanban``), so it is styled directly and
  is not touched by any view inheritance at all.

Uninstalling
------------
Uninstalling removes only the extra CSS classes and the stylesheet. The
underlying CRM views are restored exactly as shipped by Odoo. No data is
ever touched.
    """,
    'author': 'Mohammed Juraige P N',
    'license': 'LGPL-3',
    'depends': ['crm'],
    'data': [
        'security/crm_modern_theme_security.xml',
        'views/crm_theme_views.xml',
        
    ],
    'assets': {
        'web.assets_backend': [
            'crm_modern_theme/static/src/scss/01_variables.scss',
            'crm_modern_theme/static/src/scss/02_kanban.scss',
            'crm_modern_theme/static/src/scss/03_list_form.scss',
            'crm_modern_theme/static/src/scss/04_misc.scss',
            'crm_modern_theme/static/src/xml/kanban_renderer.xml',
            'crm_modern_theme/static/src/js/group_patch.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
