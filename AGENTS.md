# Flight School Management - Kilo Project Instructions

This workspace contains custom Odoo 19 modules. All generated or modified code must follow Odoo 19 conventions and the project's existing module structure.

## Odoo Version

Target Odoo version: **19.0**

Use Odoo 19 patterns:
- Use `<list>` views, not legacy `<tree>`.
- Use direct XML attributes such as `invisible="..."`, `readonly="..."`, `required="..."`; do not use legacy `attrs`.
- Prefer `models.Constraint` for SQL constraints where applicable.
- Use `models.Index` for explicit database indexes where applicable.
- Use `@api.model_create_multi` for batch-safe `create()` overrides.
- Use `@api.ondelete(at_uninstall=False)` instead of blocking `unlink()` where appropriate.

## Coding Style

- Keep imports at the top of Python files.
- Import order: standard library, third-party/Odoo, local imports.
- Avoid imports inside methods unless there is a strong reason.
- Use descriptive variable names.
- Avoid unclear names such as `data`, `info`, `tmp`, `obj`, `item`, `result`, `vals`, `recs`, `cnt`, `amt` unless the name is an established Odoo API parameter.
- Follow existing module naming and file organization.

## Odoo ORM Rules

- Avoid `search()` inside loops.
- Prefer batch operations on recordsets.
- Prefer `read_group()` for aggregation.
- Prefer `search_read()` when dictionary output is needed.
- Use `mapped`, `filtered`, and recordset operations idiomatically.
- Computed fields must declare complete `@api.depends` dependencies.
- Stored computed fields must be used when fields are searched, grouped, or filtered often.
- Monetary fields must define `currency_field`.
- `Many2one` fields should define suitable `ondelete`.

## Security Rules

Before committing or finalizing changes, check:

- No hardcoded secrets, tokens, API keys, or passwords.
- User input is validated.
- Raw SQL uses parameters, never string interpolation.
- Controllers use appropriate `auth`.
- `csrf=False` is used only when justified.
- `sudo()` is narrow, explicit, and justified.
- ACLs exist for every new model.
- Record rules are considered for business data.
- Error messages do not leak sensitive details.

## XML / Views

- Use Odoo 19 `<list>` views.
- Ensure XML IDs are stable and unique.
- Do not duplicate `name` attributes in XML records.
- Use `xpath` inheritance carefully and narrowly.
- Keep menus, actions, and views in logical files.

## Manifest Rules

- Declare all module dependencies in `__manifest__.py`.
- Add security files before views/data that depend on them.
- Add data files in deterministic order.
- Avoid loading demo/test data as normal production data.

## Testing / Validation

For meaningful changes, verify:
- module install or upgrade works,
- affected views load,
- access rights are correct,
- business flow works manually or through tests,
- no obvious N+1 ORM pattern was introduced.

## Project Kilo Skills

This repository includes a project-local Kilo skill at `.kilo/skills/flight-school-odoo-19/SKILL.md`.

Use it as the workspace-specific bridge to the relevant parts of `https://github.com/unclecatvn/agent-skills/tree/main/skills`:
- `odoo-19.0` for Odoo 19 development guidance,
- `code-review` for review and verification discipline,
- `mcp-builder` only when building MCP tools,
- `payment-integration` only when implementing payment features.

Do not apply upstream Odoo 17/18 rules to this workspace unless explicitly working on a migration or compatibility review.
