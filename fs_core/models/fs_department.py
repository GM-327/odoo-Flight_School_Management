# -*- coding: utf-8 -*-
# Part of Flight School Management System

from odoo import fields, models


class FsDepartment(models.Model):
    """Departments within the Flight School."""
    
    _name = 'fs.department'
    _description = 'Flight School Department'
    _order = 'sequence, name'

    name = fields.Char(string='Department Name', required=True, translate=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    manager_id = fields.Many2one('res.users', string='Manager')
    parent_id = fields.Many2one('fs.department', string='Parent Department')
    child_ids = fields.One2many('fs.department', 'parent_id', string='Sub-Departments')
    note = fields.Text(string='Note')

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'The department code must be unique!',
    )
