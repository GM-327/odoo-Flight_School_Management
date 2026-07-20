# Flight School Management - Antigravity Agent Guidelines

This workspace contains custom Odoo 19 modules located under `addons/Flight_School_Management`. All code generated or modified in this workspace must adhere strictly to Odoo 19 conventions, repository architecture, and project guidelines.

## Upstream Skill References & Local Packs
- **Upstream Reference Pack**: [unclecatvn/agent-skills](https://github.com/unclecatvn/agent-skills/tree/main/skills) (`skills/odoo-19.0`, `skills/code-review`, `skills/mcp-builder`, `skills/payment-integration`).
- **Local Skill Pack**: [.kilo/skills/flight-school-odoo-19/SKILL.md](file:///d:/Odoo19/server/addons/Flight_School_Management/.kilo/skills/flight-school-odoo-19/SKILL.md) and [.agents/skills/flight-school-odoo-19/SKILL.md](file:///d:/Odoo19/server/addons/Flight_School_Management/.agents/skills/flight-school-odoo-19/SKILL.md).

## Project Subagent Modes (.kilo/agent)
When performing complex architectural tasks or tracing execution flow:
- **Planner Agent** ([.kilo/agent/planner.md](file:///d:/Odoo19/server/addons/Flight_School_Management/.kilo/agent/planner.md)): Use when designing new features, breaking work into incremental testable phases, and identifying affected models/views/security/data files.
- **Odoo Code Tracer Agent** ([.kilo/agent/odoo-code-tracer.md](file:///d:/Odoo19/server/addons/Flight_School_Management/.kilo/agent/odoo-code-tracer.md)): Use to trace execution from controllers, buttons, computed fields, onchange handlers, cron jobs, and server actions through `super()`, ORM operations, security rules, and side effects.

## External Intelligence: SocratiCode
- **SocratiCode Docker Container**: Running locally via Docker ([giancarloerra/SocratiCode](https://github.com/giancarloerra/socraticode)).
- **Purpose**: Codebase semantic search, dependency graph resolution, symbol-level impact analysis, and token-optimized context retrieval.

## Runtime & Server Environment
- **Target Odoo Version**: 19.0 Community Edition
- **Python Executable**: `D:\Odoo19\python\python.exe`
- **Launcher Path**: `D:\Odoo19\server\odoo-bin -c "D:\Odoo19\server\odoo.conf"`
- **Local DB Configuration**: `db_name = odoo-demo`, `db_port = 5433`
- **Addon Suite Modules**: `fs_core`, `fs_fleet`, `fs_people`, `fs_training`, `fs_documents`, `fs_scheduling`, `fs_flights`

## Odoo 19 Code & XML Conventions
1. **Views**: Use `<list>` views instead of legacy `<tree>`.
2. **View Attributes**: Use direct XML attributes (`invisible="..."`, `readonly="..."`, `required="..."`); do NOT use legacy `attrs` or `states`.
3. **ORM Models & Constraints**:
   - Use `@api.model_create_multi` for batch `create()` overrides.
   - Use `@api.ondelete(at_uninstall=False)` instead of blocking `unlink()`.
   - Prefer `models.Constraint` and `models.Index` where explicit constraints/indexes are needed.
   - Calculated fields must specify complete `@api.depends(...)`.
   - `Monetary` fields must declare `currency_field`.
   - `Many2one` fields must specify appropriate `ondelete`.
4. **ORM Performance**:
   - Avoid `search()` inside loops; batch operations on recordsets.
   - Use `search_read()` or `read_group()` for aggregation and dictionary readouts.
   - Use `mapped()` and `filtered()` idiomatically.
5. **Security & Data Access**:
   - Every model must have corresponding access control rules in `ir.model.access.csv`.
   - Minimize `sudo()` calls; restrict to strict minimum required scope.
   - SQL queries must use parameters; never use raw string interpolation.

## Run and Debug Configurations
- Launch configurations are defined in [launch.json](file:///d:/Odoo19/server/addons/Flight_School_Management/.vscode/launch.json).
- Default debug tasks are defined in [tasks.json](file:///d:/Odoo19/server/addons/Flight_School_Management/.vscode/tasks.json).
