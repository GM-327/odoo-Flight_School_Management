# Module Development

Guide to creating and extending modules in the Flight School system.

---

## Module Structure

```
fs_your_module/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── your_model.py
├── views/
│   ├── your_model_views.xml
│   └── menu_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── security_rules.xml
├── data/
│   └── your_data.xml
├── demo/
│   └── demo_data.xml
└── static/
    └── description/
        └── icon.png
```

---

## Creating a Module

### 1. __manifest__.py

```python
{
    'name': 'Flight School Your Module',
    'version': '19.0.1.0.0',
    'category': 'Aviation/Flight School',
    'summary': 'Short description',
    'description': """
Long description here.
    """,
    'author': 'Your Name',
    'license': 'LGPL-3',
    'depends': ['fs_core'],
    'data': [
        'security/ir.model.access.csv',
        'views/your_model_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
```

### 2. Model Definition

```python
# models/your_model.py
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class YourModel(models.Model):
    _name = 'fs.your.model'
    _description = 'Your Model Description'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], default='draft')

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if len(record.name) < 3:
                raise ValidationError(_("Name must be at least 3 characters."))
```

### 3. Views (XML)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Form View -->
    <record id="view_your_model_form" model="ir.ui.view">
        <field name="name">fs.your.model.form</field>
        <field name="model">fs.your.model</field>
        <field name="arch" type="xml">
            <form string="Your Model">
                <header>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="description"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <!-- List View -->
    <record id="view_your_model_list" model="ir.ui.view">
        <field name="name">fs.your.model.list</field>
        <field name="model">fs.your.model</field>
        <field name="arch" type="xml">
            <list>
                <field name="name"/>
                <field name="state"/>
            </list>
        </field>
    </record>

    <!-- Action -->
    <record id="action_your_model" model="ir.actions.act_window">
        <field name="name">Your Model</field>
        <field name="res_model">fs.your.model</field>
        <field name="view_mode">list,form</field>
    </record>
</odoo>
```

### 4. Security (CSV)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_your_model_user,fs.your.model.user,model_fs_your_model,fs_core.group_flight_school_user,1,0,0,0
access_your_model_manager,fs.your.model.manager,model_fs_your_model,fs_core.group_flight_school_manager,1,1,1,1
```

---

## Extending Existing Models

```python
from odoo import fields, models

class Aircraft(models.Model):
    _inherit = 'fs.aircraft'

    your_new_field = fields.Char(string='New Field')
```

---

## Common Field Types

| Type | Example |
|------|---------|
| Char | `fields.Char(string='Name')` |
| Text | `fields.Text(string='Description')` |
| Integer | `fields.Integer(string='Count')` |
| Float | `fields.Float(string='Amount', digits=(10,2))` |
| Boolean | `fields.Boolean(string='Active')` |
| Date | `fields.Date(string='Date')` |
| Datetime | `fields.Datetime(string='Timestamp')` |
| Selection | `fields.Selection([('a','A'),('b','B')])` |
| Many2one | `fields.Many2one('res.partner', string='Partner')` |
| One2many | `fields.One2many('model', 'field_id')` |
| Many2many | `fields.Many2many('model', string='Tags')` |

---

## Best Practices

1. **Prefix models** with `fs.` (e.g., `fs.your.model`)
2. **Depend on fs_core** for security groups
3. **Use translations** with `_("Text")`
4. **Add access rights** for all models
5. **Write tests** for business logic

---

**← Previous**: [Development Setup](Development-Setup) | **Next**: [API Reference](API-Reference) →
