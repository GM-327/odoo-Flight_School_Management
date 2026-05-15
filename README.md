# Flight School Management for Odoo 19

<p align="center">
  <img src="https://img.shields.io/badge/Odoo-19.0-875A7B?style=for-the-badge&logo=odoo&logoColor=white" alt="Odoo 19.0"/>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/PostgreSQL-13+-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL 13+"/>
  <img src="https://img.shields.io/badge/License-LGPL--3.0-blue?style=for-the-badge" alt="LGPL-3.0"/>
</p>

Flight School Management is a modular Odoo 19 addon suite for managing flight
school operations. It covers fleet readiness, personnel records, training
programs, document compliance, mission scheduling, and daily flight execution in
one integrated workflow.

The suite is designed for aviation training organizations that need auditable
records, structured training workflows, and operational visibility across
students, instructors, aircraft, schedules, and completed flights.

---

## Table of contents

- [Key features](#key-features)
- [Addon modules](#addon-modules)
- [Requirements and dependencies](#requirements-and-dependencies)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage examples](#usage-examples)
- [Project structure](#project-structure)
- [Development and validation](#development-and-validation)
- [Documentation standards](#documentation-standards)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

---

## Key features

- **Central settings and security**: shared Flight School menus, departments,
  access groups, and system-wide configuration.
- **Fleet management**: aircraft categories, aircraft types, aircraft records,
  airworthiness state, maintenance thresholds, and certificate expiry tracking.
- **People management**: students, instructors, pilots, administrative staff,
  licenses, ranks, qualifications, English levels, medical classes, and linked
  Odoo user accounts.
- **Training management**: class types, training classes, enrollments, flight
  disciplines, flight activities, missions, hour requirements, completion
  tracking, and training dashboards.
- **Document management**: document types, entity links, upload workflows,
  version history, current-version previews, and expiry status synchronization.
- **Scheduling**: planned flights, routes, cancellation reasons, pilot
  functions, custom activities, crew-member search, conflict detection, batch
  scheduling, and timeline views.
- **Flight operations**: daily and simulator operations boards, scheduled-flight
  publishing, actual time tracking, cancellation workflows, ADD flights,
  schedule import, deletion confirmation, and hour recalculation.

---

## Addon modules

| Addon | Purpose | Key dependencies | Module docs |
|-------|---------|------------------|-------------|
| `fs_core` | Shared settings, departments, security groups, menus, and base configuration. | `base`, `base_setup`, `auth_signup` | [README](fs_core/README.rst) |
| `fs_fleet` | Aircraft categories, aircraft types, aircraft records, fleet dashboard, maintenance and certificate awareness. | `fs_core`, `mail` | [README](fs_fleet/README.rst) |
| `fs_people` | Students, instructors, pilots, staff, qualifications, licenses, medical and English-level tracking. | `fs_core`, `mail` | [README](fs_people/README.rst) |
| `fs_training` | Training classes, class types, enrollments, missions, activities, requirements, and progress tracking. | `fs_core`, `fs_people`, `fs_fleet`, `mail` | [README](fs_training/README.rst) |
| `fs_documents` | Document types, uploads, versions, previews, expiry tracking, and related-record shortcuts. | `web`, `fs_core`, `fs_people`, `fs_training` | [README](fs_documents/README.rst) |
| `fs_scheduling` | Scheduled flights, crew-member view, routes, pilot functions, conflict checks, timeline views, and scheduling wizards. | `fs_core`, `fs_training`, `fs_fleet`, `fs_people`, `mail`, `web_timeline` | [README](fs_scheduling/README.rst) |
| `fs_flights` | Daily operations, simulator operations, flight logs, schedule publishing, cancellations, and hour distribution. | `fs_scheduling`, `fs_fleet`, `fs_training`, `fs_people`, `mail`, `bus` | [README](fs_flights/README.rst) |

Install the modules you need, or install the full suite for the complete
end-to-end workflow.

---

## Requirements and dependencies

### Runtime requirements

| Component | Minimum | Notes |
|-----------|---------|-------|
| Odoo | 19.0 | The manifests and assets target Odoo 19. |
| Python | 3.10+ | Use the Python version supported by your Odoo 19 deployment. |
| PostgreSQL | 13+ | PostgreSQL 15+ is recommended for production. |
| Operating system | Linux or Windows | Linux is recommended for production Odoo hosting. |

### Odoo addon dependencies

The Flight School addons use standard Odoo modules (`base`, `base_setup`,
`auth_signup`, `mail`, `web`, and `bus`) plus the external `web_timeline` addon
for scheduling timeline views.

> **Important:** Install or make `web_timeline` available in `addons_path` before
> installing `fs_scheduling` or the full suite.

### Python dependencies

This repository contains Odoo addons and does not vendor a separate Python
requirements file. Install the Python packages required by your Odoo 19 server
from the Odoo distribution you use, then add this repository to the server's
`addons_path`.

### Development tooling

The repository includes Node-based formatting tools for frontend/XML assets:

```bash
npm install
npx prettier --check "**/*.{js,xml,css,md}"
```

---

## Installation

The commands below assume that `odoo-bin` is available from your Odoo 19 server
installation and that this repository is cloned as a custom addons directory.
Adjust paths for your deployment.

### 1. Clone or copy the addons

```bash
# Example custom addons location
mkdir -p /opt/odoo/custom/addons
cd /opt/odoo/custom/addons
git clone https://github.com/GM-327/odoo-Flight_School_Management.git Flight_School_Management
```

On Windows, place the repository in an Odoo addons path, for example:

```powershell
git clone https://github.com/GM-327/odoo-Flight_School_Management.git D:\Odoo19\server\addons\Flight_School_Management
```

### 2. Add the repository to `addons_path`

Example `odoo.conf` excerpt:

```ini
[options]
db_host = localhost
db_port = 5432
db_user = odoo
db_password = <set-a-secure-password>
addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom/addons/Flight_School_Management,/opt/odoo/custom/addons
```

Use environment-specific secrets or protected configuration management for
production credentials. Do not commit real database passwords.

### 3. Install external addon dependencies

Make sure `web_timeline` is present in one of the configured addons paths. It is
required by `fs_scheduling`.

### 4. Create or select a database

```bash
createdb flight_school
```

Alternatively, create the database from the Odoo database manager if it is
enabled in your environment.

### 5. Install the modules

Install the complete suite from the command line:

```bash
odoo-bin -c /path/to/odoo.conf -d flight_school \
  -i fs_core,fs_fleet,fs_people,fs_training,fs_documents,fs_scheduling,fs_flights \
  --stop-after-init
```

Or install the modules from **Apps** in Odoo after updating the apps list. Odoo
will resolve manifest dependencies, but the recommended installation order is:

1. `fs_core`
2. `fs_fleet` and `fs_people`
3. `fs_training`
4. `fs_documents`
5. `fs_scheduling`
6. `fs_flights`

### 6. Start Odoo

```bash
odoo-bin -c /path/to/odoo.conf -d flight_school
```

---

## Configuration

After installation, open the **Flight School** menus in Odoo and configure the
suite in this order:

1. **Core settings and security**
   - Assign users to the appropriate Flight School security groups.
   - Configure shared settings and departments.
2. **Fleet**
   - Configure aircraft categories and aircraft types.
   - Register aircraft with current hours, status, maintenance dates, and
     certificate expiry dates.
3. **People**
   - Configure ranks, license types, qualification types, English levels, and
     medical classes.
   - Create students, instructors, pilots, and administrative staff.
   - Add qualifications and expiry dates.
4. **Training**
   - Configure disciplines, flight types, activities, class requirements, class
     types, and missions.
   - Create training classes and enroll students.
5. **Documents**
   - Configure document entity types and document types.
   - Upload required files and monitor expiry status from dashboards.
6. **Scheduling**
   - Configure pilot functions, routes, cancellation reasons, callsign settings,
     and buffer times.
   - Use the scheduling wizard to generate planned flights.
7. **Flights**
   - Configure operations board behavior.
   - Publish scheduled flights and manage daily operations.

---

## Usage examples

### Workflow: create the training foundation

1. Register aircraft categories, aircraft types, and aircraft.
2. Create instructor and student records.
3. Define class types, hour requirements, flight activities, and missions.
4. Create a training class and enroll students.

Example from an Odoo shell:

```python
student = env['fs.student'].create({
    'name': 'Student Pilot',
    'callsign': 'SP01',
    'email': 'student@example.invalid',
})

training_class = env['fs.training.class'].create({
    'name': 'Initial Flight Training 2026-A',
    'class_type_id': class_type.id,
    'start_date': fields.Date.today(),
})

enrollment = env['fs.student.enrollment'].create({
    'student_id': student.id,
    'training_class_id': training_class.id,
    'instructor_id': instructor.id,
    'status': 'active',
})
```

### Workflow: generate and publish a schedule

1. Open the scheduling wizard.
2. Select active enrollments and available instructors.
3. Review generated lines, routes, aircraft types, and ADD missions.
4. Assign times, aircraft, and callsigns.
5. Confirm the schedule.
6. Publish the day to flight operations.

Example from an Odoo shell:

```python
wizard = env['fs.scheduling.wizard'].create({
    'date': fields.Date.today(),
    'selected_enrollment_ids': [(6, 0, enrollment_ids)],
    'selected_instructor_ids': [(6, 0, instructor_ids)],
})
wizard.action_next_step()
wizard.action_schedule()

scheduled_flights = env['fs.scheduled.flight'].search([
    ('date', '=', fields.Date.today()),
])
scheduled_flights.action_publish_day()
```

### Workflow: complete a flight and distribute hours

```python
flight = env['fs.flight'].search([('status', '=', 'scheduled')], limit=1)
flight.action_start_flight()
flight.write({
    'actual_departure': 8.0,
    'actual_arrival': 9.2,
})
flight.action_complete_flight()
```

Completing a flight updates applicable aircraft totals, personnel totals, and
enrollment hour ledgers. If a completed flight is corrected, signed hour deltas
are used so previous totals can be subtracted before corrected totals are
applied.

---

## Project structure

```text
Flight_School_Management/
|-- fs_core/                  # Shared settings, security, departments, menus
|-- fs_fleet/                 # Aircraft categories, types, records, dashboard
|-- fs_people/                # Personnel, qualifications, user links, dashboard
|-- fs_training/              # Training classes, enrollments, missions, hours
|-- fs_documents/             # Document types, uploads, versions, expiry status
|-- fs_scheduling/            # Planned flights, crew view, wizard, timeline
|-- fs_flights/               # Operations boards, flight logs, hour updates
|-- .github/                  # Pull request templates and repository metadata
|-- .kilo/                    # Local automation commands and agent configs
|-- CONTRIBUTING.md           # Contribution guidelines
|-- SECURITY.md               # Security policy
|-- LICENSE                   # LGPL-3.0 license text
`-- README.md                 # Project overview and setup guide
```

Each addon contains its own manifest, security rules, data files, views, and
module-specific `README.rst`.

---

## Development and validation

### Update or install modules during development

```bash
# Upgrade the full suite after code changes
odoo-bin -c /path/to/odoo.conf -d flight_school \
  -u fs_core,fs_fleet,fs_people,fs_training,fs_documents,fs_scheduling,fs_flights \
  --stop-after-init
```

### Run Odoo tests

```bash
odoo-bin -c /path/to/odoo.conf -d test_db --test-enable \
  -i fs_core,fs_fleet,fs_people,fs_training,fs_documents,fs_scheduling,fs_flights \
  --stop-after-init
```

### Run syntax and documentation checks

```bash
python -m compileall -q fs_core fs_fleet fs_people fs_training fs_documents fs_scheduling fs_flights
```

If Node dependencies are installed, validate frontend/XML formatting:

```bash
npm install
npx prettier --check "**/*.{js,xml,css,md}"
```

Recommended checks before submitting a change:

- Start Odoo and upgrade affected modules.
- Exercise the changed workflow in the Odoo UI.
- Run Python syntax checks.
- Run relevant Odoo tests.
- Update module `README.rst` files and docstrings when behavior changes.

---

## Documentation standards

- Root-level documentation belongs in this `README.md`.
- Module-specific documentation belongs in each addon's `README.rst`.
- Python modules, models, public methods, wizards, and migrations use
  Google-style docstrings.
- Complex or non-obvious business logic should include concise inline comments.
- Links should be checked when documentation is updated.

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full
process.

Basic contribution workflow:

1. Fork the repository.
2. Create a focused feature or fix branch.
3. Follow existing Odoo and Flight School coding patterns.
4. Add or update tests and documentation where appropriate.
5. Run validation checks locally.
6. Open a pull request with a clear summary and testing notes.

---

## Security

Do not open public issues for security vulnerabilities. Follow the reporting
process in [SECURITY.md](SECURITY.md).

Production recommendations:

- Use HTTPS.
- Keep Odoo and addon dependencies updated.
- Restrict PostgreSQL and Odoo administration access.
- Set `list_db = False` for public deployments.
- Use strong passwords and, where possible, two-factor authentication.
- Maintain tested backups.

---

## License

This project is licensed under the GNU Lesser General Public License v3.0 or
later (LGPL-3.0-or-later). See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [Odoo S.A.](https://www.odoo.com/) for the Odoo ERP framework.
- [European Union Aviation Safety Agency (EASA)](https://www.easa.europa.eu/)
  for aviation safety references.
- Flight School Management contributors and maintainers.
