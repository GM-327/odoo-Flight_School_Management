# Development Setup

Setting up a local development environment for the Flight School Management System.

---

## Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.10 - 3.12 | Runtime |
| PostgreSQL | 13+ | Database |
| Git | 2.34+ | Version control |
| VS Code | Latest | Recommended IDE |

---

## Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/GM-327/odoo-Flight_School_Management.git
cd odoo-Flight_School_Management

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create database
createdb flight_school_dev

# 5. Configure odoo.conf
cp odoo.conf.example odoo.conf
# Edit with your database settings

# 6. Install modules
./odoo-bin -c odoo.conf -d flight_school_dev -i fs_core,fs_fleet,fs_people --stop-after-init

# 7. Start development server
./odoo-bin -c odoo.conf --dev=all
```

---

## Development Configuration

### odoo.conf for Development

```ini
[options]
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
db_name = flight_school_dev

http_port = 8069
workers = 0

addons_path = addons,odoo/addons

log_level = debug
log_handler = :DEBUG
```

### Debug Mode

Enable developer mode:
- URL: Add `?debug=1` to any URL
- Assets debug: `?debug=assets`
- Full debug: `?debug=all`

---

## VS Code Setup

### Recommended Extensions

- Python
- Pylance
- XML Tools
- GitLens
- Odoo Snippets

### settings.json

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.analysis.extraPaths": [
    "${workspaceFolder}/odoo",
    "${workspaceFolder}/addons"
  ],
  "editor.formatOnSave": true,
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true
}
```

### launch.json (Debugging)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Odoo",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/odoo-bin",
      "args": ["-c", "odoo.conf", "--dev=all"],
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Database Management

### Create Database

```bash
createdb flight_school_dev
```

### Drop Database

```bash
dropdb flight_school_dev
```

### Reset Database

```bash
dropdb flight_school_dev && createdb flight_school_dev
./odoo-bin -c odoo.conf -d flight_school_dev -i fs_core --stop-after-init
```

---

## Common Commands

| Task | Command |
|------|---------|
| Start server | `./odoo-bin -c odoo.conf` |
| Start with dev mode | `./odoo-bin -c odoo.conf --dev=all` |
| Install module | `./odoo-bin -c odoo.conf -d db -i module --stop-after-init` |
| Upgrade module | `./odoo-bin -c odoo.conf -d db -u module --stop-after-init` |
| Run tests | `./odoo-bin -c odoo.conf -d db --test-enable -i module --stop-after-init` |
| Shell access | `./odoo-bin shell -c odoo.conf -d db` |

---

## Hot Reload

With `--dev=all`, Odoo automatically:
- Reloads Python files on change
- Recompiles assets
- Reloads XML views (with page refresh)

---

**Next**: [Module Development](Module-Development) →
