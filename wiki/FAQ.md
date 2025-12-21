# Frequently Asked Questions (FAQ)

Common questions about the Flight School Management System.

## General Questions

### What is the Flight School Management System?

An open-source ERP solution built on Odoo 19 for aviation training organizations managing aircraft, students, instructors, and regulatory compliance.

### Is this software free to use?

Yes! Released under LGPL-3.0 license - free to use, modify, and distribute.

### What Odoo version is required?

**Odoo 19.0** - not compatible with earlier versions without modifications.

---

## Installation & Setup

### What are the minimum requirements?

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4 GB | 8 GB+ |
| CPU | 2 cores | 4+ cores |
| Python | 3.10 | 3.12 |
| PostgreSQL | 13 | 15+ |

### How do I install the system?

See the complete [Installation Guide](Installation-Guide).

---

## User Management

### What user roles are available?

| Role | Description |
|------|-------------|
| **User** | Basic read access |
| **Instructor** | Manage students and training |
| **Manager** | Full operational access |
| **Administrator** | System configuration |

### How do I reset a password?

Go to **Settings → Users → Select User → Action → Change Password**

---

## Fleet Management

### How do I add a new aircraft?

**Flight School → Fleet → Aircraft → Create** - fill in registration, make/model, and status.

### How do I track maintenance?

Each aircraft has a Maintenance tab for scheduling and logging maintenance activities.

---

## Personnel Management

### How do I enroll a new student?

**Flight School → People → Students → Create** - enter student info and assign instructor.

### Can instructors see only their students?

Yes! Record rules restrict instructors to their assigned students.

---

## Technical Questions

### How do I backup the system?

```bash
# Database backup
pg_dump -U odoo flight_school > backup.sql
```

### Where are log files?

Default: `/var/log/odoo/odoo.log` (or as configured in odoo.conf)

---

## Getting More Help

1. 📖 Check the [Wiki](Home)
2. 🔍 Search [Issues](https://github.com/GM-327/odoo-Flight_School_Management/issues)
3. 💬 Ask in [Discussions](https://github.com/GM-327/odoo-Flight_School_Management/discussions)
