# Database Schema

Data model reference for the Flight School Management System.

---

## Core Models

### fs.aircraft

Aircraft registry.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| registration | Char | Aircraft registration (unique) |
| make | Char | Manufacturer |
| model | Char | Model name |
| serial_number | Char | Serial number |
| year | Integer | Year of manufacture |
| category_id | Many2one | → fs.aircraft.category |
| type_id | Many2one | → fs.aircraft.type |
| status | Selection | available, maintenance, grounded, retired |
| total_flight_hours | Float | Computed total hours |
| active | Boolean | Record active flag |

### fs.aircraft.category

Aircraft categories.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | Char | Category name |
| code | Char | Short code |
| description | Text | Description |

### fs.aircraft.type

Specific aircraft types.

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | Char | Type name (e.g., Cessna 172S) |
| category_id | Many2one | → fs.aircraft.category |
| manufacturer | Char | Manufacturer name |

---

## People Models

### fs.person

Base person model (abstract).

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Primary key |
| name | Char | Full name |
| date_of_birth | Date | Birth date |
| email | Char | Email address |
| phone | Char | Phone number |
| address | Text | Mailing address |
| rank_id | Many2one | → fs.rank |
| active | Boolean | Active flag |

### fs.student

Students (inherits fs.person).

| Field | Type | Description |
|-------|------|-------------|
| training_program | Selection | PPL, CPL, ATPL, etc. |
| instructor_id | Many2one | → fs.instructor |
| start_date | Date | Training start date |
| state | Selection | active, on_hold, completed, withdrawn |
| license_ids | One2many | → fs.person.license |
| medical_ids | One2many | → fs.person.medical |

### fs.instructor

Instructors (inherits fs.person).

| Field | Type | Description |
|-------|------|-------------|
| employee_id | Char | Employee ID |
| instructor_rating | Selection | CFI, CFII, MEI |
| student_ids | One2many | → fs.student |
| qualification_ids | One2many | → fs.person.qualification |

### fs.pilot

Qualified pilots.

| Field | Type | Description |
|-------|------|-------------|
| license_type | Selection | PPL, CPL, ATPL |
| license_number | Char | License number |
| total_hours | Float | Total flight hours |

---

## Supporting Models

### fs.person.license

License records.

| Field | Type | Description |
|-------|------|-------------|
| person_id | Many2one | → fs.person |
| license_type_id | Many2one | → fs.license.type |
| number | Char | License number |
| issue_date | Date | Issue date |
| expiry_date | Date | Expiration date |
| issuing_authority | Char | Issuing authority |

### fs.person.medical

Medical certificates.

| Field | Type | Description |
|-------|------|-------------|
| person_id | Many2one | → fs.person |
| medical_class_id | Many2one | → fs.medical.class |
| exam_date | Date | Examination date |
| expiry_date | Date | Expiration date |
| limitations | Text | Any limitations |

### fs.rank

Military/organizational ranks.

| Field | Type | Description |
|-------|------|-------------|
| name | Char | Rank name |
| code | Char | Rank code |
| sequence | Integer | Sort order |

---

## Relationships Diagram

```
fs.aircraft.category
        │
        ├── fs.aircraft.type
        │
        └── fs.aircraft
        
fs.person (abstract)
        │
        ├── fs.student ──── fs.instructor
        │       │
        │       ├── fs.person.license
        │       └── fs.person.medical
        │
        ├── fs.instructor
        │
        └── fs.pilot
```

---

## Accessing via Shell

```python
./odoo-bin shell -c odoo.conf -d flight_school

# Query aircraft
>>> self.env['fs.aircraft'].search([])

# Check schema
>>> self.env['fs.aircraft']._fields.keys()
```

---

**← Previous**: [API Reference](API-Reference) | **Next**: [Testing Guide](Testing-Guide) →
