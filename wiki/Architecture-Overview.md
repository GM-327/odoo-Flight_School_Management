# Architecture Overview

Technical documentation describing the system architecture and design patterns.

## 📋 Table of Contents

- [System Architecture](#system-architecture)
- [Module Structure](#module-structure)
- [Data Flow](#data-flow)
- [Security Model](#security-model)
- [Technology Stack](#technology-stack)
- [Integration Points](#integration-points)

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Web UI     │  │  Mobile App  │  │     External Systems     │  │
│  │  (Browser)   │  │  (Future)    │  │    (REST API Clients)    │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
└─────────┼─────────────────┼───────────────────────┼─────────────────┘
          │                 │                       │
          ▼                 ▼                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER (Odoo 19)                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                     Odoo Web Framework                       │   │
│  │  (Werkzeug WSGI + OWL JavaScript Framework)                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐   │
│  │   fs_core   │  │  fs_fleet   │  │  fs_people  │  │  ...    │   │
│  │  (Settings) │  │  (Aircraft) │  │ (Personnel) │  │         │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬────┘   │
│         │                │                │              │         │
│  ┌──────┴────────────────┴────────────────┴──────────────┴─────┐   │
│  │                    Odoo ORM Layer                            │   │
│  │        (Object-Relational Mapping + Business Logic)          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    PostgreSQL Database                       │   │
│  │                  (Transactional Storage)                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌────────────────────┐  ┌──────────────────────────────────────┐  │
│  │   File Storage     │  │          Redis (optional)            │  │
│  │   (Attachments)    │  │     (Session/Cache in production)    │  │
│  └────────────────────┘  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Web UI** | User interface, form rendering, user interactions |
| **OWL Framework** | Reactive frontend components |
| **Controllers** | HTTP request handling, routing |
| **Models** | Business logic, data validation, ORM |
| **Views** | XML view definitions, form/list layouts |
| **Security** | Access control, record rules, groups |
| **PostgreSQL** | Data persistence, transactions |

---

## Module Structure

### Flight School Module Suite

```
Flight_School_Management/
│
├── fs_core/                        # 🔧 Core Settings Module
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── res_config_settings.py  # Configuration model
│   ├── security/
│   │   ├── security_groups.xml     # User groups definition
│   │   └── ir.model.access.csv     # Access rights
│   └── views/
│       ├── res_config_settings_views.xml
│       └── menu_views.xml
│
├── fs_fleet/                       # ✈️ Fleet Management Module
│   ├── __init__.py
│   ├── __manifest__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── fs_aircraft.py          # Aircraft model
│   │   ├── fs_maintenance.py       # Maintenance tracking
│   │   └── fs_flight_log.py        # Flight logging
│   ├── security/
│   │   ├── security_rules.xml
│   │   └── ir.model.access.csv
│   ├── views/
│   │   ├── fs_aircraft_views.xml
│   │   ├── fs_maintenance_views.xml
│   │   └── menu_views.xml
│   ├── data/
│   │   └── fs_aircraft_data.xml    # Demo/default data
│   └── reports/
│       └── aircraft_report.xml
│
└── fs_people/                      # 👥 Personnel Module
    ├── __init__.py
    ├── __manifest__.py
    ├── models/
    │   ├── __init__.py
    │   ├── fs_student.py           # Student model
    │   ├── fs_instructor.py        # Instructor model
    │   ├── fs_license.py           # License tracking
    │   └── fs_medical.py           # Medical certificates
    ├── security/
    │   ├── security_rules.xml
    │   └── ir.model.access.csv
    ├── views/
    │   ├── fs_student_views.xml
    │   ├── fs_instructor_views.xml
    │   └── menu_views.xml
    └── wizards/
        └── fs_enrollment_wizard.py
```

### Module Dependencies

```
                    base
                      │
                      ▼
                  fs_core
                 /       \
                /         \
               ▼           ▼
          fs_fleet      fs_people
               \         /
                \       /
                 ▼     ▼
              fs_training  (planned)
                    │
                    ▼
             fs_scheduling (planned)
```

### Manifest Example

```python
# fs_fleet/__manifest__.py
{
    'name': 'Flight School Fleet',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Aircraft and fleet management',
    'description': """...""",
    'author': 'Ghazi Marzouk',
    'license': 'LGPL-3',
    'depends': ['fs_core', 'mail'],
    'data': [
        'security/security_rules.xml',
        'security/ir.model.access.csv',
        'views/fs_aircraft_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
```

---

## Data Flow

### Request Processing

```
1. User Action (Browser)
        │
        ▼
2. HTTP Request → Werkzeug Router
        │
        ▼
3. Controller → Business Logic
        │
        ▼
4. Model Layer (ORM)
        │
        ├── Field Validation
        ├── Compute Methods
        ├── Constraints
        └── Triggers
        │
        ▼
5. PostgreSQL Transaction
        │
        ▼
6. Response → JSON/HTML
        │
        ▼
7. UI Update (OWL)
```

### ORM Data Operations

```python
# CREATE - Records creation
aircraft = self.env['fs.aircraft'].create({
    'registration': 'N123AB',
    'make': 'Cessna',
    'model': '172S Skyhawk',
})

# READ - Querying records
cessnas = self.env['fs.aircraft'].search([
    ('make', '=', 'Cessna'),
    ('status', '=', 'available'),
])

# UPDATE - Modifying records
aircraft.write({
    'status': 'maintenance',
    'total_hours': aircraft.total_hours + 1.5,
})

# DELETE - Removing records
aircraft.unlink()
```

### Computed Fields

```python
class Aircraft(models.Model):
    _name = 'fs.aircraft'
    
    total_flight_hours = fields.Float(
        compute='_compute_total_hours',
        store=True
    )
    
    @api.depends('flight_log_ids.duration')
    def _compute_total_hours(self):
        for aircraft in self:
            aircraft.total_flight_hours = sum(
                aircraft.flight_log_ids.mapped('duration')
            )
```

---

## Security Model

### Multi-Layer Security

```
┌─────────────────────────────────────────────────────────┐
│                    Layer 1: Authentication              │
│              (Login, Session, 2FA optional)             │
├─────────────────────────────────────────────────────────┤
│                    Layer 2: User Groups                 │
│           (Role-based access control - RBAC)            │
├─────────────────────────────────────────────────────────┤
│                  Layer 3: Access Rights                 │
│          (Model-level CRUD permissions)                 │
├─────────────────────────────────────────────────────────┤
│                  Layer 4: Record Rules                  │
│         (Row-level security, domain filters)            │
├─────────────────────────────────────────────────────────┤
│                  Layer 5: Field Access                  │
│        (Field-level visibility, groups attr)            │
└─────────────────────────────────────────────────────────┘
```

### Security Groups

```xml
<!-- security/security_groups.xml -->
<odoo>
    <record id="module_category_flight_school" model="ir.module.category">
        <field name="name">Flight School</field>
        <field name="sequence">10</field>
    </record>

    <record id="group_flight_school_user" model="res.groups">
        <field name="name">User</field>
        <field name="category_id" ref="module_category_flight_school"/>
    </record>

    <record id="group_flight_school_instructor" model="res.groups">
        <field name="name">Instructor</field>
        <field name="category_id" ref="module_category_flight_school"/>
        <field name="implied_ids" eval="[(4, ref('group_flight_school_user'))]"/>
    </record>

    <record id="group_flight_school_manager" model="res.groups">
        <field name="name">Manager</field>
        <field name="category_id" ref="module_category_flight_school"/>
        <field name="implied_ids" eval="[(4, ref('group_flight_school_instructor'))]"/>
    </record>

    <record id="group_flight_school_admin" model="res.groups">
        <field name="name">Administrator</field>
        <field name="category_id" ref="module_category_flight_school"/>
        <field name="implied_ids" eval="[(4, ref('group_flight_school_manager'))]"/>
    </record>
</odoo>
```

### Access Rights (CSV)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_aircraft_user,fs.aircraft.user,model_fs_aircraft,group_flight_school_user,1,0,0,0
access_aircraft_instructor,fs.aircraft.instructor,model_fs_aircraft,group_flight_school_instructor,1,1,0,0
access_aircraft_manager,fs.aircraft.manager,model_fs_aircraft,group_flight_school_manager,1,1,1,1
```

### Record Rules

```xml
<!-- Only instructors can see their assigned students -->
<record id="rule_student_instructor" model="ir.rule">
    <field name="name">Instructors: Own Students</field>
    <field name="model_id" ref="model_fs_student"/>
    <field name="domain_force">[('instructor_id.user_id', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('group_flight_school_instructor'))]"/>
</record>
```

---

## Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.10-3.12 | Core language |
| Odoo | 19.0 | ERP Framework |
| PostgreSQL | 13-16 | Database |
| Werkzeug | 3.0.x | WSGI toolkit |
| Jinja2 | 3.1.x | Templating |

### Frontend

| Technology | Purpose |
|------------|---------|
| OWL | Odoo Web Library (reactive components) |
| JavaScript ES6+ | Client-side logic |
| SCSS/CSS | Styling |
| XML | View definitions |

### Infrastructure

| Component | Purpose |
|-----------|---------|
| Nginx | Reverse proxy, SSL termination |
| Redis | Session storage, caching (production) |
| Let's Encrypt | SSL certificates |
| systemd | Service management |

---

## Integration Points

### REST API

Odoo provides built-in REST-like endpoints:

```python
# External API call example
import xmlrpc.client

url = 'http://localhost:8069'
db = 'flight_school'
username = 'admin'
password = 'admin'

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

# Query data
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
aircraft = models.execute_kw(
    db, uid, password,
    'fs.aircraft', 'search_read',
    [[['status', '=', 'available']]],
    {'fields': ['registration', 'make', 'model']}
)
```

### Custom API Controllers

```python
from odoo import http

class FlightSchoolAPI(http.Controller):
    
    @http.route('/api/v1/aircraft', type='json', auth='user')
    def get_aircraft(self, **kwargs):
        aircraft = http.request.env['fs.aircraft'].search([])
        return aircraft.read(['registration', 'make', 'model', 'status'])
    
    @http.route('/api/v1/aircraft/<int:id>', type='json', auth='user')
    def get_aircraft_by_id(self, id, **kwargs):
        aircraft = http.request.env['fs.aircraft'].browse(id)
        return aircraft.read(['registration', 'make', 'model', 'status'])[0]
```

### Webhooks (Automation)

```python
class Aircraft(models.Model):
    _name = 'fs.aircraft'
    _inherit = ['mail.thread']
    
    def write(self, vals):
        result = super().write(vals)
        if 'status' in vals and vals['status'] == 'grounded':
            self._notify_maintenance_team()
        return result
    
    def _notify_maintenance_team(self):
        # Send notification via webhook, email, etc.
        pass
```

---

## Performance Considerations

### Database Optimization

- Use `store=True` for frequently queried computed fields
- Add database indexes for search fields
- Use `sudo()` sparingly in loops

### Caching

```python
from odoo.tools import ormcache

class Aircraft(models.Model):
    _name = 'fs.aircraft'
    
    @ormcache('self.id')
    def _get_maintenance_due_date(self):
        # Expensive calculation cached
        return self._calculate_next_maintenance()
```

### Batch Operations

```python
# Preferred: Batch operations
aircraft_ids = self.env['fs.aircraft'].search([('status', '=', 'available')])
aircraft_ids.write({'last_checked': fields.Date.today()})

# Avoid: Loop with individual writes
for aircraft in aircraft_ids:
    aircraft.write({'last_checked': fields.Date.today()})  # Bad!
```

---

**← Previous**: [Database Schema](Database-Schema) | **Next**: [API Reference](API-Reference) →
