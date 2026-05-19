---
name: flight-school-odoo-19
description: >-
  Project-local Odoo 19 skill for Flight School Management. Use when creating,
  modifying, reviewing, tracing, or securing custom Odoo modules in this
  workspace. This skill maps the relevant upstream unclecatvn/agent-skills
  packs to the local Kilo environment without vendoring irrelevant skill packs.
---

# Flight School Odoo 19 Skill

This workspace targets Odoo 19.0 and uses custom modules under the Flight School Management repository.

Upstream reference pack:
- `https://github.com/unclecatvn/agent-skills/tree/main/skills`

## Relevant Upstream Skills

Use these upstream skill concepts for this repository:

- `skills/odoo-19.0` - primary reference for Odoo 19 ORM, XML views, security, reports, OWL, actions, data files, manifests, migrations, and tests.
- `skills/code-review` - review discipline, verification gates, and evidence-based completion claims.
- `skills/mcp-builder` - only when building or changing MCP servers/tools for Kilo or other assistants.
- `skills/payment-integration` - only when implementing payment providers, webhooks, checkout flows, or payment reconciliation.

Do not use these by default:

- `skills/odoo-17.0` and `skills/odoo-18.0` - this repository targets Odoo 19.0.
- `skills/dtg-base` - only relevant if a module explicitly depends on DTGBase utilities.
- `skills/slide` - not relevant to Odoo module development.
- `skills/writing-skills` - only relevant when authoring or revising Kilo skills.
- `skills/brainstorming` - optional for early ideation; prefer the project `planner` subagent for implementation planning.

## Kilo Skill Usage

When working in this repository:

- Use the available `odoo-19` skill for Odoo 19 API and XML guidance.
- Use `odoo-orm-expert` for ORM-heavy changes, domains, computed fields, and performance-sensitive queries.
- Use `odoo-security` for ACLs, record rules, controllers, `sudo()`, and raw SQL review.
- Use `odoo-code-review` when reviewing Odoo Python/XML changes.
- Use the project `planner` subagent for feature implementation plans.
- Use the project `odoo-code-tracer` subagent to trace execution from buttons, controllers, cron jobs, computed fields, constraints, and server actions.

## Odoo 19 Rules

- Use `<list>` views, not legacy `<tree>`.
- Use direct XML attributes such as `invisible="..."`, `readonly="..."`, and `required="..."`; do not use legacy `attrs`.
- Use `@api.model_create_multi` for `create()` overrides.
- Prefer `@api.ondelete(at_uninstall=False)` over blocking `unlink()` for validation.
- Prefer `models.Constraint` and `models.Index` where explicit constraints or indexes are needed.
- Avoid `search()` inside loops; batch with recordsets, `read_group()`, or `search_read()`.
- Define complete `@api.depends` paths for computed fields.
- Define `currency_field` on `fields.Monetary`.
- Define suitable `ondelete` behavior on `Many2one` fields.

## Validation Checklist

Before calling work complete:

- Confirm affected module manifests declare dependencies and load files in deterministic order.
- Confirm security files cover new models and business data.
- Confirm views use Odoo 19 XML syntax and stable XML IDs.
- Confirm no hardcoded secrets, unsafe raw SQL, broad `sudo()`, or leaking error messages were introduced.
- Confirm the affected module can install or upgrade, or explicitly state why that validation was not run.
