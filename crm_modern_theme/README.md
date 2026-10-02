# CRM Modern Theme — for Odoo 19

A visual-only refresh of the CRM app: Pipeline/Opportunities kanban board,
Leads/Opportunities lists, and the Lead/Opportunity form. Built to look like
a modern SaaS CRM board (soft neutral background, elevated cards with a
hover lift, a colour-cycled gradient strip per pipeline column, pill tags,
cleaner typography) without touching any business logic.

**v1.0 (19.0) update — ported from the 18.0 version, with 3 real fixes.**
This module was originally built and verified against Odoo 18.0. To port it
to 19.0, every view id, xpath target, and CSS selector it depends on was
re-checked line-by-line against the actual `odoo/odoo` 19.0 branch source
(not from memory). Almost everything carried over unchanged — the 4 CRM
view ids, their root tags, and the `o_opportunity_kanban` class are all
identical in 19.0. But 3 selectors turned out to be wrong and were fixed:

1. **List header sort icon** — Odoo renamed `.o_list_sortable_caret` (18.0)
   to `.o_list_sortable_icon` (19.0). Without this fix the sort arrow in the
   list header would have stayed dark-on-dark and been hard to see against
   the new gradient header band.
2. **Kanban column progress bar** — the selector targeted a wrapper class,
   `.o_kanban_counter_progress`, that never actually existed in the real DOM
   on *either* 18.0 or 19.0 (it was a naming guess in the original module).
   The real wrapper is `.o_column_progress`, confirmed in
   `column_progress.xml` on both versions. Fixed so the slim pill-shaped
   progress bar styling actually renders now.
3. **Empty-state "no records" message** — same kind of issue:
   `.o_view_nocontent_content` was never a real class; the actual wrapper is
   `.o_nocontent_help` (confirmed in `no_content_helpers.xml` on both
   versions). Fixed so the muted text colour actually applies.

None of these three were going to *break* anything (a CSS selector that
matches nothing simply has no effect — it can't throw an error), but they
were silently doing nothing. They're real fixes now, not just a version
bump.

**Everything below this point is unchanged from the 18.0 version** except
where noted, since the visual design itself didn't need to change for 19.0.

## What's colourful now

- Each pipeline **column** gets a solid gradient header band (cycling
  through 6 colour pairs) and a soft tinted body background — using Odoo's
  own theming CSS variables (`--KanbanGroup-background`) rather than
  fighting specificity, which is the same mechanism Odoo's own coding
  guidelines describe for re-theming kanban components.
- Cards stay white/light so text stays easy to read, but each one carries
  a left-border accent in its column's colour, and a colour-tinted shadow
  on hover — so the board reads as colourful while staying legible.
- The drag-over highlight (Odoo's own `.o_kanban_hover`) is retinted via
  the same CSS-variable approach — Odoo's core rule uses `!important`, so
  rather than fight it, this module simply feeds it different colours.
- The **list view** header is now a gradient band too, with a subtle
  colour-tinted zebra stripe on alternating rows.
- The **form** gets a soft ambient colour wash behind the sheet and an
  accent-coloured top border on the sheet itself, plus the gradient
  statusbar from before.

## What's interactive (not just decorative)

- **Dragging a card** gets a colourful glow, a slight tilt, and a scale-up
  — using Odoo's own `o_dragged` class, which it already adds to the
  element being dragged (`web/core/utils/draggable_hook_builder.js`).
- **Dragging over a column** highlights that column with a soft tinted
  background and a gentle pulsing ring — using Odoo's own `o_kanban_hover`
  class, which its kanban renderer already adds/removes on
  `onGroupEnter`/`onGroupLeave` (`kanban_renderer.js`). This isn't a guess
  or a hack: it's the exact hook Odoo built for this purpose.
- **Hovering a card** lifts it and adds a colour-tinted shadow; the
  assignee avatar's ring shifts to the secondary accent colour at the same
  time.
- **Clicking/holding a card** gives a tactile little press-down effect, and
  keyboard focus shows a visible accent ring (accessibility-friendly).
- **Priority stars and tags** scale up slightly on hover across kanban,
  list, and form.
- **Stage statusbar buttons** on the form light up on hover before you
  click, and the current stage gets an indigo→violet gradient.
- Each pipeline **column** gets its own gradient accent strip (cycling
  through 6 colours), and that same colour carries down as a left-border
  accent on every card in that column — so a card visually "belongs" to
  its column at a glance, purely through CSS, with zero dependency on
  stage data (so it can never show a "wrong" colour for a stage).

## What this module actually does

1. **Adds 4 SCSS files** to the `web.assets_backend` bundle. That's it —
   plain CSS rules, compiled by Odoo's own asset pipeline. No JavaScript,
   no Python.
2. **Adds one CSS class** to the root tag of 4 existing CRM views (Leads
   kanban, Leads list, Opportunities list, Lead/Opportunity form), using
   Odoo's *additive* attribute syntax:
   ```xml
   <attribute name="class" add="o_crm_theme_list" separator=" "/>
   ```
   This appends a class — it never replaces or removes anything, so it
   can't collide with another module doing the same thing on the same view.
   The Pipeline kanban itself isn't touched by any inheritance at all — it
   already ships with its own unique class (`o_opportunity_kanban`), so
   it's styled directly.

Every CSS selector in the module starts with one of: `.o_opportunity_kanban`,
`.o_crm_theme_kanban_leads`, `.o_crm_theme_list`, `.o_crm_theme_form`. None
of those classes exist anywhere outside CRM, so nothing here can leak into
Sales, Invoicing, Inventory, or any other app.

## How I verified this against Odoo 19, not memory

I pulled the actual Odoo source from GitHub (`odoo/odoo`) for both the
`18.0` and `19.0` branches — `addons/crm/views` for the 4 view ids this
module inherits, and `addons/web/static/src/views` for every core
kanban/list/form/field OWL template and SCSS file a selector in this module
touches. I diffed the two branches' relevant templates directly rather than
assuming 19.0 looks like 18.0, which is how the 3 fixes above were found.
I also re-compiled the full SCSS bundle with the real `dart-sass` compiler
after every fix — zero errors, zero warnings — and validated the view XML
is well-formed.

## Honest caveats — please read

- **I can't promise zero risk, only very low risk.** Any change to a
  database, however small, deserves a test first. CSS-only changes are
  about as safe as Odoo customisation gets (worst case a selector doesn't
  match anything and simply has no visual effect — it can't throw an error
  or take down a screen), but the 4 view inheritances do touch real
  `ir.ui.view` records, so I'd still install this on a duplicate/staging
  database first, click through Pipeline, Leads, list, and form views, and
  only then put it on production.
- This was checked against the **19.0 stable branch** view structure (and
  diffed against 18.0 to catch what changed). If you're on a heavily-
  customized fork, or another CRM-theming module already adds the very same
  marker classes another way, do a quick visual check after install.
- One tiny known cosmetic overlap: Odoo's kanban cards have a built-in,
  rarely-used "set a colour" option in their own 3-dot menu. If someone
  manually picks a colour that way on a specific card, that card will show
  both Odoo's own colour accent and this theme's column-accent border at
  the same time. Nothing breaks — it's just two colour accents stacking on
  a card most people never touch.
- I used exactly **one `!important`** in the whole module (overriding the
  Bootstrap `.fs-5` utility class on the card title, since that title needs
  to be visually smaller than Bootstrap's 1.25rem default) — flagged in
  `02_kanban.scss` with a comment so it's easy to find.

## Installing

1. Copy the `crm_modern_theme` folder into your Odoo `addons` path.
2. Update Apps List (Apps → top-right ⋮ → Update Apps List), or restart
   the server with `-u crm_modern_theme` / `--dev=all` style restart.
3. Search "CRM Modern Theme" in Apps and install it.
4. Hard-refresh the browser (Ctrl+Shift+R) so the new asset bundle loads.

## Uninstalling

Uninstall like any other module. The 4 view inheritances are removed
automatically, restoring the original CRM views exactly as Odoo ships
them. No data is ever touched.

## Customizing the palette

Everything is driven by CSS variables in
`static/src/scss/01_variables.scss` — change `--crm-accent` to switch the
whole theme's accent colour in one place, or edit `--crm-bg`/`--crm-surface`
for a different background tone.
