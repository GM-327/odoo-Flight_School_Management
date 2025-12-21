# Code Style Guide

Coding standards for the Flight School Management System.

---

## Python Style

### General Rules

- Follow **PEP 8**
- Follow **Odoo coding guidelines**
- Use **4 spaces** for indentation (no tabs)
- Maximum line length: **120 characters**
- Use **UTF-8** encoding

### File Header

```python
# -*- coding: utf-8 -*-
# Part of Flight School Management System
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
```

### Import Order

```python
# 1. Standard library
import logging
from datetime import datetime

# 2. Third-party
import requests

# 3. Odoo
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
```

---

## Model Definition

### Class Structure

```python
class Aircraft(models.Model):
    _name = 'fs.aircraft'
    _description = 'Aircraft'
    _order = 'registration'
    _inherit = ['mail.thread']

    # 1. Default method
    def _default_status(self):
        return 'available'

    # 2. Fields (in order: char, text, numbers, dates, selections, relations)
    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    total_hours = fields.Float(string='Total Hours', digits=(10, 1))
    registration_date = fields.Date(string='Registration Date')
    status = fields.Selection([
        ('available', 'Available'),
        ('maintenance', 'Maintenance'),
    ], default=_default_status)
    category_id = fields.Many2one('fs.aircraft.category', string='Category')
    
    # 3. Compute and search methods
    @api.depends('flight_log_ids.duration')
    def _compute_total_hours(self):
        for record in self:
            record.total_hours = sum(record.flight_log_ids.mapped('duration'))

    # 4. Constraints
    @api.constrains('registration')
    def _check_registration(self):
        for record in self:
            if not record.registration:
                raise ValidationError(_("Registration is required."))

    # 5. Onchange methods
    @api.onchange('category_id')
    def _onchange_category(self):
        if self.category_id:
            self.name = self.category_id.name

    # 6. CRUD methods
    @api.model
    def create(self, vals):
        # Custom logic
        return super().create(vals)

    # 7. Action methods
    def action_set_maintenance(self):
        self.write({'status': 'maintenance'})

    # 8. Business methods
    def _calculate_maintenance_due(self):
        # Business logic
        pass
```

---

## Naming Conventions

### Models

| Type | Convention | Example |
|------|------------|---------|
| Model name | Lowercase, dot-separated | `fs.aircraft` |
| Class name | CamelCase | `FsAircraft` |
| Table name | Auto-generated | `fs_aircraft` |

### Fields

| Type | Convention | Example |
|------|------------|---------|
| Regular fields | Lowercase, underscore | `total_hours` |
| Many2one | Suffix `_id` | `category_id` |
| One2many | Suffix `_ids` | `flight_log_ids` |
| Many2many | Suffix `_ids` | `tag_ids` |
| Computed | Same as regular | `total_hours` |

### Methods

| Type | Convention | Example |
|------|------------|---------|
| Compute | `_compute_<field>` | `_compute_total_hours` |
| Onchange | `_onchange_<field>` | `_onchange_category` |
| Constraint | `_check_<rule>` | `_check_registration` |
| Action | `action_<name>` | `action_confirm` |
| Private | `_<name>` | `_calculate_hours` |

---

## XML Guidelines

### IDs

```xml
<!-- Views: view_<model>_<type> -->
<record id="view_fs_aircraft_form" model="ir.ui.view">

<!-- Actions: action_<model> -->
<record id="action_fs_aircraft" model="ir.actions.act_window">

<!-- Menus: menu_<name> -->
<menuitem id="menu_flight_school_aircraft">
```

### View Structure

```xml
<form string="Aircraft">
    <header>
        <!-- Status bar, buttons -->
    </header>
    <sheet>
        <div class="oe_title">
            <!-- Main title field -->
        </div>
        <group>
            <!-- Fields -->
        </group>
        <notebook>
            <!-- Tabs -->
        </notebook>
    </sheet>
    <div class="oe_chatter">
        <!-- Chatter -->
    </div>
</form>
```

---

## Linting

### Using Ruff

```bash
# Check
ruff check .

# Fix automatically
ruff check --fix .
```

### Configuration (ruff.toml)

```toml
line-length = 120
target-version = "py310"

[lint]
select = ["E", "F", "W"]
ignore = ["E501"]
```

---

## Commit Messages

```
[module] Short description (max 50 chars)

Longer explanation if needed. Wrap at 72 characters.

Fixes #123
```

Examples:
- `[fs_fleet] Add maintenance scheduling feature`
- `[fs_people] Fix license expiration calculation`
- `[fs_core] Update security groups`

---

## Documentation

### Docstrings

```python
def calculate_flight_hours(self, start_date, end_date):
    """Calculate total flight hours in date range.
    
    Args:
        start_date: Start of period
        end_date: End of period
        
    Returns:
        float: Total flight hours
        
    Raises:
        ValidationError: If dates are invalid
    """
    pass
```

---

**← Previous**: [Testing Guide](Testing-Guide) | **Next**: [Deployment Guide](Deployment-Guide) →
